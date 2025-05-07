from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import enum

class PositionEnum(str, enum.Enum):
    사원 = "사원"
    사장 = "사장"

class VacationStatusEnum(str, enum.Enum):
    대기 = "대기"
    승인 = "승인"
    거절 = "거절"

# 사용자 회원가입용
class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: PositionEnum
    join_date: Optional[date] = None
    password: str
    base_salary: Optional[int] = None

# 사용자 응답용
class UserOut(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: PositionEnum
    join_date: Optional[date]
    base_salary: Optional[int]

    class Config:
        from_attributes = True

# 출퇴근용
class AttendanceRecord(BaseModel):
    user_id: int
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None

# 급여 명세용
class PayrollOut(BaseModel):
    id: int
    user_id: int
    pay_date: date
    amount: int

    class Config:
        from_attributes = True

# 휴가 신청용
class VacationRequestCreate(BaseModel):
    user_id: int
    request_date: date

class VacationRequestOut(BaseModel):
    id: int
    user_id: int
    request_date: date
    status: VacationStatusEnum

    class Config:
        from_attributes = True  # ✅ 최종 수정 완료
