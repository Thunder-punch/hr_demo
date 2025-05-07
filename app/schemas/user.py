# /schemas/user.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from models import PositionEnum

class UserUpdate(BaseModel):
    """
    직원 정보 수정 시 사용되는 스키마
    (email, position, base_salary 등을 선택적으로 업데이트)
    """
    email: Optional[EmailStr] = None
    position: Optional[PositionEnum] = None
    base_salary: Optional[int] = None
