# /mnt/data/app/routers/user.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

# 내부 모듈 임포트
from app.schemas.user import UserUpdate
from app.utils.logger import log
from database import get_db
from models import User, Attendance

router = APIRouter(prefix="/user", tags=["직원"])

@router.put("/{user_id}")
def update_user_info(user_id: int, update: UserUpdate, db: Session = Depends(get_db)):
    """
    직원 정보(이메일, 직급, 기본급 등)를 수정하는 엔드포인트.
    - PUT /user/{user_id}
    - Body: {"email": "...", "position": "...", "base_salary": ...}
    """
    log(f"✏️ 직원 정보 수정 요청: user_id={user_id}, 수정내용={update.dict(exclude_unset=True)}", tag="USER")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        log(f"❌ 존재하지 않는 사용자 ID: {user_id}", tag="USER")
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    update_data = update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    log(f"✅ 직원 정보 수정 완료: {user.name} ({user.email})", tag="USER")
    return {"message": f"직원 정보가 수정되었습니다. (ID: {user_id})"}


@router.post("/attendance/clock-in")
def clock_in(name: str, db: Session = Depends(get_db)):
    """
    특정 직원의 출근 시간을 현재 시각으로 기록하는 엔드포인트.
    - 예: POST /user/attendance/clock-in?name=정태우
    """
    log(f"⏰ 출근 기록 요청: name={name}", tag="ATTENDANCE")

    user = db.query(User).filter(User.name == name).first()
    if not user:
        log(f"❌ 존재하지 않는 사용자: {name}", tag="ATTENDANCE")
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")

    new_record = Attendance(
        user_id=user.id,
        clock_in=datetime.now(),
        clock_out=None
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    log(f"✅ 출근 기록 완료: user_id={user.id}, clock_in={new_record.clock_in}", tag="ATTENDANCE")
    return {"message": f"{user.name}님의 출근 기록이 추가되었습니다."}


@router.patch("/attendance/clock-out")
def clock_out(name: str, db: Session = Depends(get_db)):
    """
    특정 직원의 가장 최근 출근 기록(퇴근시간이 비어있는 레코드)에 퇴근 시간을 현재 시각으로 업데이트.
    - 예: PATCH /user/attendance/clock-out?name=정태우
    """
    log(f"⏳ 퇴근 기록 요청: name={name}", tag="ATTENDANCE")

    user = db.query(User).filter(User.name == name).first()
    if not user:
        log(f"❌ 존재하지 않는 사용자: {name}", tag="ATTENDANCE")
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")

    # 아직 퇴근시간이 기록되지 않은 Attendance 레코드
    attendance = db.query(Attendance).filter(
        Attendance.user_id == user.id,
        Attendance.clock_out == None
    ).order_by(Attendance.clock_in.desc()).first()

    if not attendance:
        log(f"⚠️ 출근 기록이 없습니다: user_id={user.id}", tag="ATTENDANCE")
        raise HTTPException(status_code=404, detail="출근 기록이 없습니다.")

    attendance.clock_out = datetime.now()
    db.commit()
    db.refresh(attendance)

    log(f"✅ 퇴근 기록 완료: user_id={user.id}, clock_out={attendance.clock_out}", tag="ATTENDANCE")
    return {"message": f"{user.name}님의 퇴근 기록이 등록되었습니다."}
