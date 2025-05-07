from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
import os

from app.utils.email.send_salary_mail import send_salary_mail
from app.utils.pdf.generate_reportlab_pdf import generate_payroll_pdf
from app.models import User, Payroll
from app.database import get_db

payroll_router = APIRouter()


@payroll_router.get("/payroll/pdf/{user_id}")
async def generate_pdf(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    payroll = db.query(Payroll).filter(Payroll.user_id == user.id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")

    payroll_data = {
        "base_salary": payroll.base_salary,
        "overtime_allowance": payroll.overtime_allowance,
        "other_allowances": payroll.other_allowances,
        "total_payment": payroll.total_payment,
        "total_deduction": payroll.total_deduction,
        "actual_payment": payroll.actual_payment
    }

    # PDF 파일 경로 생성
    output_path = f"temp_payroll_{uuid4().hex}.pdf"
    pdf_path = generate_payroll_pdf(user, payroll_data, output_path)

    # ✅ 이메일 전송
    send_salary_mail(
        to_email=user.email,
        subject="급여명세서",
        body="첨부된 파일을 확인하세요.",
        attachment=pdf_path
    )

    return {"message": "급여명세서 이메일 전송 완료"}


@payroll_router.get("/payroll/send-mail/{user_id}")
async def send_payroll_via_email(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    payroll = db.query(Payroll).filter(Payroll.user_id == user.id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")

    payroll_data = {
        "base_salary": payroll.base_salary,
        "overtime_allowance": payroll.overtime_allowance,
        "other_allowances": payroll.other_allowances,
        "total_payment": payroll.total_payment,
        "total_deduction": payroll.total_deduction,
        "actual_payment": payroll.actual_payment
    }

    # PDF 파일 경로 생성
    output_path = f"temp_payroll_{uuid4().hex}.pdf"
    pdf_path = generate_payroll_pdf(user, payroll_data, output_path)

     # 이메일 전송 전에 파일 상태 확인 로그
    if not os.path.exists(pdf_path):
        print(f"🚫 PDF 파일이 존재하지 않습니다: {pdf_path}")
    else:
        file_size = os.path.getsize(pdf_path)
        print(f"📄 PDF 파일 크기: {file_size} bytes - 경로: {pdf_path}")
        if file_size < 100:
            print("⚠️ PDF 파일 크기가 너무 작습니다. 내용이 비었거나 잘못 생성됐을 수 있습니다.")

    # ✅ 이메일 전송
    send_salary_mail(
        to_email=user.email,
        subject="급여명세서",
        body="첨부된 파일을 확인하세요.",
        attachment=pdf_path
    )

    return {"message": "급여명세서 이메일 전송 완료"}
