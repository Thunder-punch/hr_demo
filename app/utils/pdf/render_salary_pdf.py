import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 폰트 경로를 절대 경로로 수정
FONT_PATH = "C:/Users/texcl/friend_env/hr_demo/app/utils/fonts/NanumGothic.ttf"

# 폰트가 존재하면 등록
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH))

def generate_payroll_pdf(user: dict, payroll: dict, output_path: str):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 50
    y = height - 50
    line_height = 20

    def line(text, indent=0):
        nonlocal y
        try:
            p.setFont("NanumGothic", 11)
        except:
            p.setFont("Helvetica", 11)
        p.drawString(x + indent, y, text)
        y -= line_height

    try:
        p.setFont("NanumGothic", 14)
    except:
        p.setFont("Helvetica-Bold", 14)
    p.drawString(x, y, "[급여 명세서]")
    y -= 40

    # 본문
    line(f"성명: {user['name']}    부서: (미정)    직급: {user['position']}")
    line(f"지급일: {payroll['pay_date']}")
    y -= 10

    line("──────────── 지급 항목 ────────────")
    line(f"기본급           : {payroll['base_salary']:,}원", indent=10)
    line(f"연장근로수당     : {payroll['overtime_allowance']:,}원", indent=10)
    line(f"야간근로수당     : {payroll['night_allowance']:,}원", indent=10)
    line(f"휴일근로수당     : {payroll['holiday_allowance']:,}원", indent=10)
    line(f"가족수당         : {payroll['family_allowance']:,}원", indent=10)
    line(f"식대             : {payroll['meal_allowance']:,}원", indent=10)
    y -= 10

    line("──────────── 공제 항목 ────────────")
    line(f"소득세           : {payroll['tax']:,}원", indent=10)
    line(f"국민연금         : {payroll['national_pension']:,}원", indent=10)
    line(f"고용보험         : {payroll['employment_insurance']:,}원", indent=10)
    line(f"건강보험         : {payroll['health_insurance']:,}원", indent=10)
    line(f"장기요양보험     : {payroll['care_insurance']:,}원", indent=10)
    line(f"노조비           : {payroll['union_fee']:,}원", indent=10)
    y -= 10

    line(f"💰 지급합계  : {payroll['total_payment']:,}원")
    line(f"📉 공제합계  : {payroll['total_deduction']:,}원")
    line(f"✅ 실수령액  : {payroll['actual_payment']:,}원")

    p.showPage()
    p.save()

    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())
