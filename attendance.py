from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models import Attendance, SessionLocal
from sqlalchemy import and_

router = APIRouter()

class AttendanceRequest(BaseModel):
    user_id: int  # 사용자 고유 ID

# 출근 기록
@router.post("/attendance/check-in")
def check_in(request: AttendanceRequest):
    db = SessionLocal()
    today = datetime.now().date()

    # 오늘 출근 기록 확인
    existing = db.query(Attendance).filter(
        and_(
            Attendance.user_id == request.user_id,
            Attendance.clock_in != None,
            Attendance.clock_in >= datetime(today.year, today.month, today.day)
        )
    ).first()

    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="이미 출근했습니다.")

    new_record = Attendance(
        user_id=request.user_id,
        clock_in=datetime.now(),
        ip_address=None  # IP 저장은 추후 추가 가능
    )

    db.add(new_record)
    db.commit()

    # 세션 닫기 전 값 추출
    clock_in_time = new_record.clock_in.strftime("%H:%M:%S")
    db.close()

    return {"message": "출근 기록 완료!", "time": clock_in_time}

# 퇴근 기록
@router.post("/attendance/check-out")
def check_out(request: AttendanceRequest):
    db = SessionLocal()
    today = datetime.now().date()

    record = db.query(Attendance).filter(
        and_(
            Attendance.user_id == request.user_id,
            Attendance.clock_in >= datetime(today.year, today.month, today.day)
        )
    ).first()

    if not record:
        db.close()
        raise HTTPException(status_code=404, detail="출근 기록이 없습니다.")

    if record.clock_out:
        db.close()
        raise HTTPException(status_code=400, detail="이미 퇴근했습니다.")

    record.clock_out = datetime.now()
    db.commit()

    # 세션 닫기 전 값 추출
    clock_out_time = record.clock_out.strftime("%H:%M:%S")
    db.close()

    return {"message": "퇴근 기록 완료!", "time": clock_out_time}

# 전체 기록 조회
@router.get("/attendance/")
def get_all_attendance():
    db = SessionLocal()
    records = db.query(Attendance).all()
    result = []
    for r in records:
        result.append({
            "user_id": r.user_id,
            "clock_in": r.clock_in.strftime("%Y-%m-%d %H:%M:%S") if r.clock_in else None,
            "clock_out": r.clock_out.strftime("%Y-%m-%d %H:%M:%S") if r.clock_out else None,
            "ip_address": r.ip_address
        })
    db.close()
    return result

# 날짜별 기록 조회
@router.get("/attendance/by-date")
def get_attendance_by_date(date: Optional[str] = Query(None, description="YYYY-MM-DD 형식의 날짜")):
    if not date:
        raise HTTPException(status_code=400, detail="날짜를 쿼리로 제공해주세요. 예: /attendance/by-date?date=2025-03-31")

    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 잘못되었습니다. 예: 2025-03-31")

    db = SessionLocal()
    start = datetime(target_date.year, target_date.month, target_date.day)
    end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    records = db.query(Attendance).filter(
        Attendance.clock_in >= start,
        Attendance.clock_in <= end
    ).all()

    result = []
    for r in records:
        result.append({
            "user_id": r.user_id,
            "clock_in": r.clock_in.strftime("%Y-%m-%d %H:%M:%S") if r.clock_in else None,
            "clock_out": r.clock_out.strftime("%Y-%m-%d %H:%M:%S") if r.clock_out else None,
            "ip_address": r.ip_address
        })
    db.close()
    return result
