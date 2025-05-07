# create_payrolls.py
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Payroll
from datetime import date

def create_payroll(user_id, pay_date):
    db: Session = SessionLocal()
    payroll = Payroll(
        user_id=user_id,
        pay_date=pay_date,
        base_salary=3000000,
        overtime_allowance=200000,
        night_allowance=100000,
        holiday_allowance=150000,
        family_allowance=50000,
        meal_allowance=100000,
        tax=150000,
        national_pension=135000,
        employment_insurance=30000,
        health_insurance=95000,
        care_insurance=12000,
        union_fee=10000,
        total_payment=3600000,
        total_deduction=432000,
        actual_payment=3168000,
    )
    db.add(payroll)
    db.commit()
    db.refresh(payroll)
    print(f"✅ 급여명세서 생성: 사용자 {user_id}, 지급일 {pay_date}")
    db.close()

if __name__ == "__main__":
    create_payroll(user_id=1, pay_date=date(2025, 4, 1))
    create_payroll(user_id=2, pay_date=date(2025, 4, 1))
    create_payroll(user_id=3, pay_date=date(2025, 4, 1))
