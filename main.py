from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import faiss
import numpy as np
import os
import json
from sentence_transformers import SentenceTransformer
from sqlalchemy import text

from database import engine, get_db
from models import Base
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import extract
from passlib.context import CryptContext
from app.models.faceattendance import router as face_router

from datetime import datetime
import requests
import json
import io
import os
from urllib.parse import quote
import asyncio

# ✅ 로거는 프로젝트 모듈이므로 맨 아래에 정리
from app.utils.logger import log, print_exception

from database import engine, get_db
from models import Base, User, PositionEnum, Payroll, Attendance
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 상단 유틸리티 함수 영역 (import 이후)
from dateutil import parser
from dateutil.relativedelta import relativedelta
import re
from datetime import timedelta


def parse_absolute_date(date_str: str):
    """절대 날짜 표현(예: '2025년 4월 3일', '2025-04-03')을 datetime.date 객체로 변환"""
    try:
        dt = parser.parse(date_str, fuzzy=True)
        return dt.date()
    except Exception as e:
        print("날짜 파싱 오류:", e)
        return None

def parse_relative_date(relative_str: str):
    """
    간단한 상대 날짜 표현을 처리합니다. 예: "2년 뒤", "3개월 후", "10일 후", "내년", "다음 달"
    """
    now = datetime.now()
    # "년" 처리
    year_match = re.search(r"(\d+)\s*년", relative_str)
    if year_match:
        years = int(year_match.group(1))
        return (now + relativedelta(years=years)).date()
    # "개월" 처리
    month_match = re.search(r"(\d+)\s*개월", relative_str)
    if month_match:
        months = int(month_match.group(1))
        return (now + relativedelta(months=months)).date()
    # "일" 처리
    day_match = re.search(r"(\d+)\s*일", relative_str)
    if day_match:
        days = int(day_match.group(1))
        return (now + timedelta(days=days)).date()
    if "내년" in relative_str:
        return (now + relativedelta(years=1)).date()
    if "다음 달" in relative_str:
        return (now + relativedelta(months=1)).date()
    return None


FONT_PATH = "C:/Users/texcl/friend_env/hr_demo/app/utils/fonts/NanumGothic.ttf"
pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH))


def load_hr_system_prompt():
    with open("prompts/instruction_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()

app = FastAPI()
app.include_router(face_router)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# 1) PDF Q&A 준비 (FAISS + chunks 로딩)
# ------------------------------
DB_DIR = os.path.join(os.path.dirname(__file__), 'data', 'db')
CLEAN_DIR = os.path.join(os.path.dirname(__file__), 'data', 'clean')

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(CLEAN_DIR, exist_ok=True)

# (1) 통합 FAISS 인덱스 만들기
index = None
index_files = sorted([f for f in os.listdir(DB_DIR) if f.endswith(".faiss")])
for f in index_files:
    fpath = os.path.join(DB_DIR, f)
    tmp_idx = faiss.read_index(fpath)
    if index is None:
        index = tmp_idx
    else:
        index.merge_from(tmp_idx)

if index is None:
    print("⚠️ FAISS 인덱스가 없습니다. PDF Q&A 불가.")
else:
    print(f"✅ 통합 FAISS 인덱스 로드 완료: {index.ntotal} vectors")

all_chunks = []
json_files = sorted([f for f in os.listdir(CLEAN_DIR) if f.endswith(".json")])
for jf in json_files:
    with open(os.path.join(CLEAN_DIR, jf), "r", encoding="utf-8") as fp:
        data = json.load(fp)
        chunk_list = data.get("chunks", [])
        all_chunks.extend(chunk_list)

print(f"✅ all_chunks 로딩 완료: 총 {len(all_chunks)}개")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embed_model = SentenceTransformer(MODEL_NAME)
print(f"✅ 임베딩 모델 로딩: {MODEL_NAME}")


# ------------------------------
# 2) Ollama LLM 호출 예시
# ------------------------------
import requests

def call_ollama_chat(context, user_query):
    prompt = f"""
다음 문단을 참고해 질문에 답하세요.

[관련 문단]
{context}

[질문]
{user_query}

[답변]
"""
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma:7b",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        data = res.json()
        return data.get("response", "").strip()
    except Exception as e:
        print("❌ Ollama 호출 오류:", e)
        return "죄송합니다. Ollama 서버와 통신에 실패했습니다."


# ------------------------------
# 3) 라우터: PDF Q&A
# ------------------------------
from pydantic import BaseModel

class PdfQARequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/pdf-qa/")
def pdf_qa(payload: PdfQARequest):
    if index is None or index.ntotal == 0:
        raise HTTPException(
            status_code=500,
            detail="FAISS 인덱스가 로드되지 않았습니다. PDF 로딩이 안 된 상태입니다."
        )
    query_vector = embed_model.encode([payload.query])
    query_vector = np.array(query_vector, dtype="float32")
    top_k = max(payload.top_k, 1)
    distances, ids = index.search(query_vector, top_k)
    retrieved_chunks = []
    for i in range(top_k):
        chunk_id = ids[0][i]
        if 0 <= chunk_id < len(all_chunks):
            retrieved_chunks.append(all_chunks[chunk_id])
    context_text = "\n\n".join(retrieved_chunks)
    answer = call_ollama_chat(context_text, payload.query)
    return {
        "answer": answer,
        "chunks": retrieved_chunks,
    }

from app.routers.user import router as user_router
app.include_router(user_router)

@app.middleware("http")
async def catch_all_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        log(f"🔥 요청 중 오류 발생: {request.method} {request.url.path}", tag="ERROR")
        print_exception()
        raise e

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Prompt(BaseModel):
    prompt: str

class RegisterUser(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    position: PositionEnum
    startDate: str
    password: str
    base_salary: int

class LoginData(BaseModel):
    email: EmailStr
    password: str

from app.utils.logger import log  # 이미 있다면 생략

@app.post("/register")
def register_user(user: RegisterUser, db: Session = Depends(get_db)):
    log(f"📥 회원가입 요청: {user.name} ({user.email})", tag="USER")
    if db.query(User).filter(User.email == user.email).first():
        log(f"❌ 중복 이메일로 회원가입 시도: {user.email}", tag="USER")
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    hashed_pw = pwd_context.hash(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        position=user.position,
        join_date=datetime.strptime(user.startDate, "%Y-%m-%d").date(),
        password_hash=hashed_pw,
        base_salary=user.base_salary
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    log(f"✅ 회원가입 완료: {new_user.name} ({new_user.email})", tag="USER")
    return {"message": "회원가입 완료"}

@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    log(f"🔐 로그인 시도: {data.email}", tag="LOGIN")
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        log(f"❌ 로그인 실패: {data.email}", tag="LOGIN")
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다.")
    log(f"✅ 로그인 성공: {user.name} ({user.email})", tag="LOGIN")
    return {"message": "로그인 성공", "position": user.position}

def calculate_work_stats(user_id: int, year: int, month: int, db: Session):
    records = db.query(Attendance).filter(
        Attendance.user_id == user_id,
        extract("year", Attendance.clock_in) == year,
        extract("month", Attendance.clock_in) == month,
        Attendance.clock_out.isnot(None)
    ).all()
    total_minutes = 0
    overtime_minutes = 0
    base_work_minutes_per_day = 8 * 60
    for r in records:
        duration = (r.clock_out - r.clock_in).total_seconds() / 60
        total_minutes += duration
        if duration > base_work_minutes_per_day:
            overtime_minutes += duration - base_work_minutes_per_day
    return {
        "total_minutes": int(total_minutes),
        "overtime_minutes": int(overtime_minutes),
        "work_hours": int(total_minutes // 60),
        "overtime_hours": int(overtime_minutes // 60)
    }

def query_ollama_instruction(prompt: str) -> dict:
    try:
        print("🟩 [DEBUG] Instruction Prompt 입력:", prompt)
        with open("prompts/instruction_prompt.txt", "r", encoding="utf-8") as f:
            template = f.read()
        full_prompt = template.replace("{prompt}", prompt)
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma:7b",
                "prompt": full_prompt,
                "stream": False
            }
        )
        response = res.json()
        raw = response.get("response", "").strip()
        print("🟩 [DEBUG] AI Instruction Raw Output:", raw)
        # JSON 형식이면 파싱하고 아니라면 그대로 반환
        if raw.startswith("{") and raw.endswith("}"):
            parsed = json.loads(raw)
            print("🟩 [DEBUG] Instruction Parsed:", parsed)
            # 만약 filter가 vacation_balance인 경우 vacation_requests로 재설정
            if parsed.get("type") == "휴가" and parsed.get("filter") == "vacation_balance":
                parsed["filter"] = "vacation_requests"
            return parsed
        else:
            # JSON이 아닌 경우 텍스트 자체를 최종 명령으로 사용
            return {"generated_text": raw}
    except Exception as e:
        print("❌ instruction 처리 중 오류:", e)
        return {"type": "fallback"}


def query_ollama_chat(prompt: str) -> str:
    try:
        print("🟦 [DEBUG] Chat Prompt 입력:", prompt)
        with open("prompts/chat_prompt.txt", "r", encoding="utf-8") as f:
            template = f.read()
        full_prompt = template.replace("{prompt}", prompt)
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma:7b",
                "prompt": full_prompt,
                "stream": False
            }
        )
        raw_chat = res.json()["response"].strip()
        print("🟦 [DEBUG] Ollama Chat Raw Output:", raw_chat)
        return raw_chat
    except Exception as e:
        print("❌ [ERROR] Chat 처리 중 오류:", e)
        return "죄송합니다, 지금은 답변할 수 없습니다."

def generate_payroll_text(user: User,
                          payroll: Payroll,
                          stats: dict,
                          hourly_wage: int,
                          base_salary: int,
                          total_payment: int,
                          total_deduction: int,
                          actual_payment: int) -> str:
    pay_date = payroll.pay_date
    return f"""
📄 [급여 명세서]

👤 성명: {user.name}       🏢 부서: (미정)       🎖 직급: {user.position.value}
📅 지급일: {pay_date}

⏰ 근무시간: {stats['work_hours']}시간   ⌛ 연장근무: {stats['overtime_hours']}시간   💵 시급: {hourly_wage:,}원

──────────── 지급 항목 ────────────
기본급           : {base_salary:,}원
연장근로수당     : {payroll.overtime_allowance:,}원
야간근로수당     : {payroll.night_allowance:,}원
휴일근로수당     : {payroll.holiday_allowance:,}원
가족수당         : {payroll.family_allowance:,}원
식대             : {payroll.meal_allowance:,}원

──────────── 공제 항목 ────────────
소득세           : {payroll.tax:,}원
국민연금         : {payroll.national_pension:,}원
고용보험         : {payroll.employment_insurance:,}원
건강보험         : {payroll.health_insurance:,}원
장기요양보험     : {payroll.care_insurance:,}원
노조비           : {payroll.union_fee:,}원

💰 지급합계  : {total_payment:,}원
📉 공제합계  : {total_deduction:,}원
✅ 실수령액  : {actual_payment:,}원
""".strip()

@app.post("/generate/")
async def generate_text(prompt: Prompt, db: Session = Depends(get_db)):
    user_input = prompt.prompt.strip()
    print("🟠 [DEBUG] /generate/ user_input:", user_input)
    parsed = query_ollama_instruction(user_input)
    print("🟠 [DEBUG] /generate/ parsed result:", parsed)
    
    # 질문에 "에 대해 알려줘"가 포함되어 있는지 확인합니다.
    # 만약 포함되어 있다면 PDF 기반 검색을 우선적으로 시도합니다.
    if "에 대해 알려줘" in user_input:
        if index is not None and index.ntotal > 0 and len(all_chunks) > 0:
            query_vector = embed_model.encode([user_input])
            query_vector = np.array(query_vector, dtype="float32")
            top_k = 3
            distances, ids = index.search(query_vector, top_k)
            retrieved_chunks = []
            for i in range(top_k):
                chunk_id = ids[0][i]
                if 0 <= chunk_id < len(all_chunks):
                    retrieved_chunks.append(all_chunks[chunk_id])
            context_text = "\n\n".join(retrieved_chunks)
            print("🟠 [DEBUG] PDF 기반 Context:", context_text[:200], "...")
            if context_text.strip():
                response_text = call_ollama_chat(context_text, user_input)
                # 만약 PDF 검색 후에도 답변이 없다면 fallback 메시지 처리
                if not response_text.strip():
                    response_text = "학습한 내용이 없습니다."
            else:
                response_text = "학습한 내용이 없습니다."
            return {
                "generated_text": response_text,
                "table_data": [],
                "download_url": None
            }
        else:
            # PDF 데이터가 존재하지 않으면 기존 chat_prompt을 사용합니다.
            response_text = query_ollama_chat(user_input)
            return {
                "generated_text": response_text,
                "table_data": [],
                "download_url": None
            }
    # 그 외(예: 일반 질문의 경우) fallback 처리: 이미 instruction_prompt에서 올바른 JSON 명령을 만들지 못했을 경우
    if parsed.get("type") == "fallback":
        print("🔴 [WARN] Instruction fallback. Chat prompt로 전환합니다.")
        response_text = query_ollama_chat(user_input)
        return {
            "generated_text": response_text,
            "table_data": [],
            "download_url": None
        }
    
    try:
        response_text = ""
        table_data = []
        download_url = ""
        if parsed.get("type") == "급여":
            # (급여 처리 로직은 기존 그대로 사용)
            name = parsed.get("target", "")
            if not name:
                users = db.query(User).all()
                if not users:
                    return {
                        "generated_text": "등록된 직원이 없습니다.",
                        "table_data": [],
                        "download_url": None
                    }
                response_lines = []
                for u in users:
                    payroll = db.query(Payroll).filter(
                        Payroll.user_id == u.id
                    ).order_by(Payroll.pay_date.desc()).first()
                    if not payroll:
                        response_lines.append(f"{u.name}님의 급여명세서가 존재하지 않습니다.")
                        continue
                    pay_date = payroll.pay_date
                    stats = calculate_work_stats(u.id, pay_date.year, pay_date.month, db)
                    hourly_wage = round(u.base_salary / (20.8 * 8))
                    base_salary = stats["work_hours"] * hourly_wage
                    total_payment = (
                        base_salary +
                        payroll.overtime_allowance +
                        payroll.night_allowance +
                        payroll.holiday_allowance +
                        payroll.family_allowance +
                        payroll.meal_allowance
                    )
                    total_deduction = (
                        payroll.tax +
                        payroll.national_pension +
                        payroll.employment_insurance +
                        payroll.health_insurance +
                        payroll.care_insurance +
                        payroll.union_fee
                    )
                    actual_payment = total_payment - total_deduction
                    payroll.work_hours = stats["work_hours"]
                    payroll.overtime_hours = stats["overtime_hours"]
                    payroll.hourly_wage = hourly_wage
                    payroll.base_salary = base_salary
                    payroll.total_payment = total_payment
                    payroll.total_deduction = total_deduction
                    payroll.actual_payment = actual_payment
                    db.commit()
                    block_text = generate_payroll_text(
                        user=u,
                        payroll=payroll,
                        stats=stats,
                        hourly_wage=hourly_wage,
                        base_salary=base_salary,
                        total_payment=total_payment,
                        total_deduction=total_deduction,
                        actual_payment=actual_payment
                    )
                    response_lines.append(block_text)
                full_text = "\n\n".join(response_lines)
                return {
                    "generated_text": full_text,
                    "table_data": [],
                    "download_url": None
                }
            user = db.query(User).filter(User.name == name).first()
            if not user:
                return {
                    "generated_text": "해당 사용자를 찾을 수 없습니다.",
                    "table_data": [],
                    "download_url": None
                }
            payroll = db.query(Payroll).filter(
                Payroll.user_id == user.id
            ).order_by(Payroll.pay_date.desc()).first()
            if not payroll:
                return {
                    "generated_text": "급여명세서가 존재하지 않습니다.",
                    "table_data": [],
                    "download_url": None
                }
            pay_date = payroll.pay_date
            stats = calculate_work_stats(user.id, pay_date.year, pay_date.month, db)
            hourly_wage = round(user.base_salary / (20.8 * 8))
            base_salary = stats["work_hours"] * hourly_wage
            total_payment = (
                base_salary +
                payroll.overtime_allowance +
                payroll.night_allowance +
                payroll.holiday_allowance +
                payroll.family_allowance +
                payroll.meal_allowance
            )
            total_deduction = (
                payroll.tax +
                payroll.national_pension +
                payroll.employment_insurance +
                payroll.health_insurance +
                payroll.care_insurance +
                payroll.union_fee
            )
            actual_payment = total_payment - total_deduction
            payroll.work_hours = stats["work_hours"]
            payroll.overtime_hours = stats["overtime_hours"]
            payroll.hourly_wage = hourly_wage
            payroll.base_salary = base_salary
            payroll.total_payment = total_payment
            payroll.total_deduction = total_deduction
            payroll.actual_payment = actual_payment
            db.commit()
            download_url = f"http://localhost:8000/payroll/pdf/{user.id}"
            response_text = generate_payroll_text(
                user=user,
                payroll=payroll,
                stats=stats,
                hourly_wage=hourly_wage,
                base_salary=base_salary,
                total_payment=total_payment,
                total_deduction=total_deduction,
                actual_payment=actual_payment
            )
        elif parsed.get("type") == "퇴직금":
            target = parsed.get("target")
            date_str = parsed.get("date") or parsed.get("value")
            retirement_date = None
            if date_str:
                retirement_date = parse_absolute_date(date_str)
                if retirement_date is None:
                    retirement_date = parse_relative_date(date_str)
            current_date = datetime.now().date()
            if retirement_date is None:
                years = 1
            else:
                years = retirement_date.year - current_date.year
                if retirement_date.month < current_date.month or (retirement_date.month == current_date.month and retirement_date.day < current_date.day):
                    years -= 1
                if years < 1:
                    years = 1
            user = db.query(User).filter(User.name == target).first()
            if not user:
                return {
                    "generated_text": "해당 사용자를 찾을 수 없습니다.",
                    "table_data": [],
                    "download_url": None
                }
            severance = user.base_salary * years
            response_text = f"{user.name}님이 {years}년 근속 후 퇴직하면 예상 퇴직금은 {severance:,}원 입니다."
            return {
                "generated_text": response_text,
                "table_data": [],
                "download_url": None
            }
        elif parsed.get("type") == "휴가":
            target = parsed.get("target")
            user = db.query(User).filter(User.name == target).first()
            if not user:
                return {
                    "generated_text": "해당 사용자를 찾을 수 없습니다.",
                    "table_data": [],
                    "download_url": None
                }
            total_allocated = 15
            stmt = text("SELECT COUNT(*) FROM vacation_requests WHERE user_id = :uid AND status = '승인'")
            result = db.execute(stmt, {"uid": user.id})
            approved_count = result.scalar() or 0
            remaining = total_allocated - approved_count
            response_text = f"{user.name}님의 잔여 휴가는 현재 {remaining}일입니다."
            return {
                "generated_text": response_text,
                "table_data": [],
                "download_url": None
            }
        elif parsed.get("type") == "출퇴근":
            target = parsed.get("target")
            filter_val = parsed.get("filter")
            user = db.query(User).filter(User.name == target).first()
            if not user:
                return {
                    "generated_text": "해당 사용자를 찾을 수 없습니다.",
                    "table_data": [],
                    "download_url": None
                }
            if filter_val == "clock_in":
                new_record = Attendance(user_id=user.id, clock_in=datetime.now())
                db.add(new_record)
                db.commit()
                clock_in_time = new_record.clock_in.strftime("%Y-%m-%d %H:%M:%S")
                response_text = f"{user.name}님의 출근 기록이 등록되었습니다. 출근 시간: {clock_in_time}"
            elif filter_val == "clock_out":
                record = db.query(Attendance).filter(
                    Attendance.user_id == user.id,
                    Attendance.clock_out == None
                ).order_by(Attendance.clock_in.desc()).first()
                if not record:
                    return {
                        "generated_text": "출근 기록이 없습니다.",
                        "table_data": [],
                        "download_url": None
                    }
                record.clock_out = datetime.now()
                db.commit()
                clock_out_time = record.clock_out.strftime("%Y-%m-%d %H:%M:%S")
                response_text = f"{user.name}님의 퇴근 기록이 등록되었습니다. 퇴근 시간: {clock_out_time}"
            elif filter_val == "worktime":
                today = datetime.now().date()
                records = db.query(Attendance).filter(
                    Attendance.user_id == user.id,
                    extract("year", Attendance.clock_in) == today.year,
                    extract("month", Attendance.clock_in) == today.month,
                    extract("day", Attendance.clock_in) == today.day
                ).all()
                if not records:
                    response_text = f"{user.name}님의 오늘 출퇴근 기록이 존재하지 않습니다."
                else:
                    details = []
                    for rec in records:
                        clock_in_str = rec.clock_in.strftime("%Y-%m-%d %H:%M:%S")
                        if rec.clock_out:
                            clock_out_str = rec.clock_out.strftime("%Y-%m-%d %H:%M:%S")
                            delta = rec.clock_out - rec.clock_in
                            total_seconds = delta.seconds
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            duration_str = f"(근무시간: {hours}시간 {minutes}분)"
                        else:
                            clock_out_str = "미등록"
                            duration_str = ""
                        details.append(f"출근: {clock_in_str}, 퇴근: {clock_out_str} {duration_str}")
                    response_text = f"{user.name}님의 오늘 출퇴근 기록:\n" + "\n".join(details)
            else:
                response_text = query_ollama_chat(user_input)
        elif parsed.get("type") == "직원" and parsed.get("filter") == "join_date":
            name = parsed.get("target")
            user = db.query(User).filter(User.name == name).first()
            if not user:
                return {
                    "generated_text": "해당 직원을 찾을 수 없습니다.",
                    "table_data": [],
                    "download_url": None
                }
            return {
                "generated_text": f"{user.name}님의 입사일은 {user.join_date}입니다.",
                "table_data": [],
                "download_url": None
            }
        elif parsed.get("type") == "직원":
            users = db.query(User).all()
            if not users:
                return {
                    "generated_text": "",
                    "table_data": [],
                    "download_url": None
                }
            table_data = []
            for u in users:
                table_data.append({
                    "이름": u.name,
                    "이메일": u.email,
                    "직급": u.position.value,
                    "기본급": u.base_salary
                })
            return {
                "generated_text": "다음은 하엘프랜즈의 전 직원 목록입니다.",
                "table_data": table_data,
                "download_url": None
            }
        if not table_data and not response_text:
            response_text = query_ollama_chat(user_input)
        return {
            "generated_text": response_text,
            "table_data": table_data,
            "download_url": download_url or None
        }
    except Exception as e:
        return {
            "generated_text": f"서버 오류 발생: {e}",
            "table_data": [],
            "download_url": None
        }
    except Exception as e:
        return {
            "generated_text": f"서버 오류 발생: {e}",
            "table_data": [],
            "download_url": None
        }

from payroll_router import router as payroll_router
app.include_router(payroll_router)

from app.routers.contract_router import contract_router
app.include_router(contract_router)

from app.models.faceattendance import router as face_attendance_router
app.include_router(face_attendance_router)
