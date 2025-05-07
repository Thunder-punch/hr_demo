import sys
import os
from dotenv import load_dotenv
from datetime import timedelta  # 📌 추가
from sqlalchemy.orm import Session  # 📌 추가


# .env 파일에서 환경 변수 로드
load_dotenv()

# 경로 추가 (app 디렉토리 경로를 추가)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 절대 경로로 임포트
from app.utils.email.send_salary_mail import send_salary_mail
from app.utils.pdf.generate_reportlab_pdf import generate_payroll_pdf
from models import Attendance  # ✅ models.py가 hr_demo/에 있을 때 정답


# 📌 [NEW] 근무시간 계산 함수
def calculate_work_and_overtime_hours(db: Session, user_id: int, pay_date):
    month_start = pay_date.replace(day=1)
    next_month = pay_date.replace(day=28) + timedelta(days=4)
    month_end = next_month.replace(day=1)

    records = (
        db.query(Attendance)
        .filter(
            Attendance.user_id == user_id,
            Attendance.clock_in >= month_start,
            Attendance.clock_in < month_end
        )
        .all()
    )

    total_work_seconds = 0
    for record in records:
        if record.clock_in and record.clock_out:
            total_work_seconds += (record.clock_out - record.clock_in).total_seconds()

    total_work_hours = round(total_work_seconds / 3600)
    overtime = max(0, total_work_hours - 8 * len(records))  # 하루 8시간 초과만 연장근무로
    return total_work_hours, overtime

# 📌 db 세션을 매개변수로 추가
def send_salary_to_employee(user, payroll, db: Session):
    filename = f"{user.name}_{payroll.pay_date}_급여명세서.pdf"

    # 💡 상대경로로 ./tmp 폴더 지정 (없으면 생성)
    tmp_dir = os.path.join(os.path.dirname(__file__), "../../tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    filepath = os.path.join(tmp_dir, filename)

    # 📌 1단계: 출퇴근기록 기반으로 근무시간 계산
    work_hours, overtime_hours = calculate_work_and_overtime_hours(db, user.id, payroll.pay_date)
    payroll.work_hours = work_hours
    payroll.overtime_hours = overtime_hours

    print("📌 1단계: payroll_sender → work_hours =", payroll.work_hours)

    # 급여명세서 PDF 생성
    generate_payroll_pdf(
        user={
            "name": user.name,
            "position": getattr(user.position, 'value', user.position)
        },
        payroll={
            "pay_date": payroll.pay_date,
            "base_salary": payroll.base_salary,
            "overtime_allowance": payroll.overtime_allowance,
            "night_allowance": payroll.night_allowance,
            "holiday_allowance": payroll.holiday_allowance,
            "family_allowance": payroll.family_allowance,
            "meal_allowance": payroll.meal_allowance,
            "tax": payroll.tax,
            "national_pension": payroll.national_pension,
            "employment_insurance": payroll.employment_insurance,
            "health_insurance": payroll.health_insurance,
            "care_insurance": payroll.care_insurance,
            "union_fee": payroll.union_fee,
            "total_payment": payroll.total_payment,
            "total_deduction": payroll.total_deduction,
            "actual_payment": payroll.actual_payment,
            "work_hours": payroll.work_hours,  # 📌 추가 반영
            "overtime_hours": payroll.overtime_hours,  # 📌 추가 반영
            "hourly_wage": payroll.hourly_wage
        },
        output_path=filepath
    )

    # 급여명세서 이메일 전송
    send_salary_mail(
        to_email=user.email,
        subject=f"[Haelfriends] {payroll.pay_date} 급여명세서",
        body=f"{user.name}님,\n\n{payroll.pay_date} 급여명세서를 첨부드립니다.",
        attachment=filepath
    )