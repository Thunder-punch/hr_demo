# app/routers/contract_router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
import os

from pydantic import BaseModel, EmailStr
# 주의: 'from app.database import get_db'가 아니라,
# 'from database import get_db' 등 프로젝트 경로에 맞게 수정
from database import get_db

from app.utils.pdf.generate_contract_pdf import generate_contract_pdf
from app.utils.email.send_salary_mail import send_salary_mail

contract_router = APIRouter()

class ContractData(BaseModel):
    employee_name: str
    employee_address: str
    position: str
    start_date: str       # "YYYY-MM-DD" 등의 형식
    contract_period: str  # 예: "1년", "2년"
    salary: int
    working_hours: str
    additional_terms: str | None = None
    email: EmailStr       # 계약서를 받을 이메일 주소

@contract_router.post("/contract/create")
async def create_contract(contract_data: ContractData, db: Session = Depends(get_db)):
    """
    입력된 계약 데이터를 바탕으로 근로계약서 PDF를 생성하고,
    이메일로 발송하는 API 엔드포인트입니다.
    """
    contract_dict = contract_data.dict()

    # PDF 파일 생성 (파일명은 임시 파일명 사용)
    output_path = f"temp_contract_{uuid4().hex}.pdf"
    pdf_path = generate_contract_pdf(contract_dict, output_path)

    # 이메일 발송 (send_salary_mail 함수를 재사용)
    email_sent = send_salary_mail(
        to_email=contract_data.email,
        subject="근로계약서",
        body="첨부된 파일을 확인하세요.",
        attachment=pdf_path
    )
    if not email_sent:
        raise HTTPException(status_code=500, detail="이메일 전송에 실패했습니다.")

    return {"message": "근로계약서 이메일 전송 완료"}
