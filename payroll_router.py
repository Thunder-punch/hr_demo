from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Payroll, User
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from urllib.parse import quote
import os
import io
from app.services.payroll_sender import send_salary_to_employee

router = APIRouter(prefix="/payroll", tags=["급여"])

# ✅ 폰트 등록
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_PATH_REGULAR = os.path.join(FONT_DIR, "NanumGothic.ttf")

if os.path.exists(FONT_PATH_REGULAR):
    pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH_REGULAR))


@router.post("/create")
def create_sample_payroll(db: Session = Depends(get_db)):
    new_payroll = Payroll(
        user_id=1,
        pay_date="2025-04-01",
        base_salary=3000000,
        overtime_allowance=200000,
        night_allowance=100000,
        holiday_allowance=150000,
        family_allowance=50000,
        meal_allowance=100000,
        tax=150000,
        national_pension=135000,
        employment_insurance=30000,
        health_insurance=95000,
        care_insurance=12000,
        union_fee=10000,
        total_payment=3600000,
        total_deduction=432000,
        actual_payment=3168000,
    )
    db.add(new_payroll)
    db.commit()
    db.refresh(new_payroll)
    return {"message": "샘플 급여명세서가 저장되었습니다.", "id": new_payroll.id}


@router.get("/latest/prettified")
def get_prettified_payroll(user_id: int, db: Session = Depends(get_db)):
    payroll = db.query(Payroll).filter(Payroll.user_id == user_id).order_by(Payroll.pay_date.desc()).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="급여명세서를 찾을 수 없습니다.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    result = f"""📄 [급여 명세서]

👤 성명: {user.name}       🏢 부서: (미정)       🎖 직급: {getattr(user.position, 'value', user.position)}
📅 지급일: {payroll.pay_date}

──────────── 지급 항목 ────────────
기본급           : {payroll.base_salary:,}원
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

💰 지급합계  : {payroll.total_payment:,}원  
📉 공제합계  : {payroll.total_deduction:,}원  
✅ 실수령액  : {payroll.actual_payment:,}원"""

    return {
        "message": result,
        "download_url": f"http://localhost:8000/payroll/pdf/{user.id}"
    }


@router.get("/pdf/{user_id}")
def download_payroll_pdf(user_id: int, db: Session = Depends(get_db)):
    print("📥 PDF 요청 들어옴:", user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    payroll = (
        db.query(Payroll)
        .filter(Payroll.user_id == user.id)
        .order_by(Payroll.pay_date.desc())
        .first()
    )
    if not payroll:
        raise HTTPException(status_code=404, detail="급여명세서를 찾을 수 없습니다.")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 50
    y = height - 50
    line_height = 20

    def line(text, indent=0):
        nonlocal y
        try:
            p.setFont("NanumGothic", 11)
        except:
            p.setFont("Helvetica", 11)
        p.drawString(x + indent, y, text)
        y -= line_height

    try:
        p.setFont("NanumGothic", 14)
    except:
        p.setFont("Helvetica-Bold", 14)
    p.drawString(x, y, "[급여 명세서]")
    y -= 40

    line(f"성명: {user.name}    부서: (미정)    직급: {getattr(user.position, 'value', user.position)}")
    line(f"지급일: {payroll.pay_date}")
    y -= 10

    line("──────────── 지급 항목 ────────────")
    line(f"기본급           : {payroll.base_salary:,}원", 10)
    line(f"연장근로수당     : {payroll.overtime_allowance:,}원", 10)
    line(f"야간근로수당     : {payroll.night_allowance:,}원", 10)
    line(f"휴일근로수당     : {payroll.holiday_allowance:,}원", 10)
    line(f"가족수당         : {payroll.family_allowance:,}원", 10)
    line(f"식대             : {payroll.meal_allowance:,}원", 10)
    y -= 10

    line("──────────── 공제 항목 ────────────")
    line(f"소득세           : {payroll.tax:,}원", 10)
    line(f"국민연금         : {payroll.national_pension:,}원", 10)
    line(f"고용보험         : {payroll.employment_insurance:,}원", 10)
    line(f"건강보험         : {payroll.health_insurance:,}원", 10)
    line(f"장기요양보험     : {payroll.care_insurance:,}원", 10)
    line(f"노조비           : {payroll.union_fee:,}원", 10)
    y -= 10

    line(f"💰 지급합계  : {payroll.total_payment:,}원")
    line(f"📉 공제합계  : {payroll.total_deduction:,}원")
    line(f"✅ 실수령액  : {payroll.actual_payment:,}원")

    try:
        p.showPage()
        p.save()
    except Exception as e:
        print("❌ PDF 저장 중 오류:", e)

    buffer.seek(0)
    filename = f"payroll_{user.name}_{payroll.pay_date}.pdf"
    encoded_filename = quote(filename)

    return StreamingResponse(buffer, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    })


@router.get("/send-mail/{user_id}")
def send_payroll_email(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    payroll = (
        db.query(Payroll)
        .filter(Payroll.user_id == user.id)
        .order_by(Payroll.pay_date.desc())
        .first()
    )
    if not payroll:
        raise HTTPException(status_code=404, detail="급여명세서를 찾을 수 없습니다.")

    send_salary_to_employee(user, payroll, db)


    return {"message": f"{user.name}님에게 급여명세서를 메일로 전송했습니다."}
