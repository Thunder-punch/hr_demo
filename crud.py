from sqlalchemy.orm import Session
from models import User, Attendance, Payroll, VacationRequest
from schemas import UserCreate, AttendanceRecord, VacationRequestCreate
from datetime import datetime, date

# 회원 생성
def create_user(db: Session, user: UserCreate):
    db_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        position=user.position,
        join_date=user.join_date,
        password=user.password,
        base_salary=user.base_salary
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 출근 기록
def record_clock_in(db: Session, user_id: int):
    record = Attendance(user_id=user_id, clock_in=datetime.now())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

# 퇴근 기록 (마지막 출근의 clock_out 갱신)
def record_clock_out(db: Session, user_id: int):
    record = db.query(Attendance).filter(Attendance.user_id == user_id, Attendance.clock_out == None).order_by(Attendance.clock_in.desc()).first()
    if record:
        record.clock_out = datetime.now()
        db.commit()
        db.refresh(record)
    return record

# 급여 내역 조회
def get_payrolls(db: Session, user_id: int):
    return db.query(Payroll).filter(Payroll.user_id == user_id).all()

# 휴가 신청
def create_vacation_request(db: Session, request: VacationRequestCreate):
    new_req = VacationRequest(
        user_id=request.user_id,
        request_date=request.request_date,
        status="대기"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req

# 전체 직원 조회 (사장용)
def get_all_users(db: Session):
    return db.query(User).all()

# 전체 휴가 신청 내역 조회 (사장용)
def get_all_vacation_requests(db: Session):
    return db.query(VacationRequest).all()