from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import record_clock_in, record_clock_out
from schemas import AttendanceRecord
from models import Attendance
from typing import List
from fastapi.responses import StreamingResponse
import csv
import io

router = APIRouter(prefix="/attendance", tags=["attendance"])

# DB 세션 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 출근 기록
@router.post("/clockin")
def clock_in(user_id: int, db: Session = Depends(get_db)):
    return record_clock_in(db, user_id)

# 퇴근 기록
@router.post("/clockout")
def clock_out(user_id: int, db: Session = Depends(get_db)):
    return record_clock_out(db, user_id)

# 전체 출퇴근 기록 조회 (사장용)
@router.get("/all", response_model=List[AttendanceRecord])
def get_all_attendance(db: Session = Depends(get_db)):
    return db.query(Attendance).all()

# CSV 다운로드용 엔드포인트
@router.get("/download")
def download_attendance_csv(db: Session = Depends(get_db)):
    records = db.query(Attendance).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User ID", "Clock In", "Clock Out"])

    for r in records:
        writer.writerow([r.id, r.user_id, r.clock_in, r.clock_out])

    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]),
                              media_type="text/csv",
                              headers={"Content-Disposition": "attachment; filename=attendance.csv"})
