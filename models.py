from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

# 기존 database.py에서 엔진과 베이스 불러오기
from database import Base

# ✅ 역할 구분용 ENUM
class PositionEnum(str, enum.Enum):
    사원 = "사원"
    사장 = "사장"

# ✅ 휴가 상태 ENUM
class VacationStatusEnum(str, enum.Enum):
    대기 = "대기"
    승인 = "승인"
    거절 = "거절"

# ✅ 사용자 테이블 (face_image_path 컬럼 추가)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    position = Column(Enum(PositionEnum), nullable=False)  # 사원 or 사장
    join_date = Column(Date, nullable=True)
    password_hash = Column(String, nullable=False)  # bcrypt 해시 저장
    base_salary = Column(Integer, nullable=True)
    face_image_path = Column(String(255), nullable=True)  # 얼굴 등록 이미지 파일 경로

# ✅ 출퇴근 기록
class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clock_in = Column(TIMESTAMP, default=datetime.now)
    clock_out = Column(TIMESTAMP, nullable=True)
    ip_address = Column(String, nullable=True)

# ✅ 휴가 신청
class VacationRequest(Base):
    __tablename__ = "vacation_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_date = Column(Date)
    status = Column(Enum(VacationStatusEnum), default="대기")

# ✅ 급여명세서 상세 필드 포함
class Payroll(Base):
    __tablename__ = "payroll"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pay_date = Column(Date, nullable=False)

    # 지급 항목
    base_salary = Column(Integer, nullable=False, default=0)           # 기본급
    overtime_allowance = Column(Integer, nullable=False, default=0)    # 연장근로수당
    night_allowance = Column(Integer, nullable=False, default=0)       # 야간근로수당
    holiday_allowance = Column(Integer, nullable=False, default=0)     # 휴일근로수당
    family_allowance = Column(Integer, nullable=False, default=0)      # 가족수당
    meal_allowance = Column(Integer, nullable=False, default=0)        # 식대

    # 공제 항목
    tax = Column(Integer, nullable=False, default=0)                   # 소득세
    national_pension = Column(Integer, nullable=False, default=0)      # 국민연금
    employment_insurance = Column(Integer, nullable=False, default=0)  # 고용보험
    health_insurance = Column(Integer, nullable=False, default=0)      # 건강보험
    care_insurance = Column(Integer, nullable=False, default=0)        # 장기요양보험
    union_fee = Column(Integer, nullable=False, default=0)             # 노동조합비

    # 합계
    total_payment = Column(Integer, nullable=False, default=0)         # 총지급액
    total_deduction = Column(Integer, nullable=False, default=0)       # 총공제액
    actual_payment = Column(Integer, nullable=False, default=0)        # 실지급액

    # 총 근무시간
    work_hours = Column(Integer, nullable=False, default=0)
    
    # 연장 근무시간
    overtime_hours = Column(Integer, nullable=False, default=0)
    
    # 시급
    hourly_wage = Column(Integer, nullable=False, default=0)

class UserFace(Base):
    __tablename__ = "user_faces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String(255), nullable=False)