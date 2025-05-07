from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import VacationRequest, User
from schemas import VacationRequestCreate, VacationRequestOut
from typing import List
from datetime import date, timedelta
import math

router = APIRouter(prefix="/vacation", tags=["vacation"])

# DB 세션 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 휴가 신청
@router.post("/request", response_model=VacationRequestOut)
def request_vacation(request: VacationRequestCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 근속 개월 계산
    today = date.today()
    months = (today.year - user.join_date.year) * 12 + (today.month - user.join_date.month)

    # 휴가 일수 계산
    if months < 12:
        allowed_days = months  # 1개월 근로시 1일씩 (최대 11일)
    else:
        allowed_days = 15      # 12개월 이상 근로 시 연 15일 고정

    # 이미 신청한 휴가 수
    used_days = db.query(VacationRequest).filter(
        VacationRequest.user_id == user.id,
        VacationRequest.status == "승인"
    ).count()

    if used_days >= allowed_days:
        raise HTTPException(status_code=400, detail="사용 가능한 휴가가 없습니다.")

    # 신청 등록
    new_req = VacationRequest(
        user_id=request.user_id,
        request_date=request.request_date,
        status="대기"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req

# 전체 휴가 신청 내역 (사장용)
@router.get("/all", response_model=List[VacationRequestOut])
def get_all_requests(db: Session = Depends(get_db)):
    return db.query(VacationRequest).all()

# 휴가 승인/거절
@router.post("/approve")
def approve_request(request_id: int, approve: bool, db: Session = Depends(get_db)):
    req = db.query(VacationRequest).filter(VacationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="휴가 신청을 찾을 수 없습니다.")
    req.status = "승인" if approve else "거절"
    db.commit()
    db.refresh(req)
    return req