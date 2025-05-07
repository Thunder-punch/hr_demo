# auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
from utils import save_user

router = APIRouter()

class User(BaseModel):
    name: str
    role: Literal["사장", "직원"]
    email: str
    phone: str

@router.post("/register/")
def register_user(user: User):
    try:
        save_user(user.dict())
        return {"message": "사용자 정보가 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
