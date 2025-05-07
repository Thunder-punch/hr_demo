import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 한글 폰트 등록 (NanumGothic)
FONT_PATH = "C:/Users/texcl/friend_env/hr_demo/app/utils/fonts/NanumGothic.ttf"
pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH))

def generate_payroll_pdf(user: dict, payroll: dict, output_path: str):
    print("📌 2단계: PDF 함수 → payroll dict =", payroll)  # ← 이 줄 추가!

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("NanumGothic", 12)

    width, height = A4
    line_height = 20
    y = height - 50

    def draw_text(text, x, y, font_size=12):
        c.setFont("NanumGothic", font_size)
        c.drawString(x, y, text)

    def draw_center(text, y, font_size=14):
        text_width = pdfmetrics.stringWidth(text, "NanumGothic", font_size)
        x = (width - text_width) / 2
        draw_text(text, x, y, font_size)

    # [제목]
    draw_center("[급여 명세서]", y, 14)
    y -= line_height * 2

    # 상단 기본 정보
    draw_text(f"👤 성명: {user['name']}", 50, y)
    draw_text(f"🏢 부서: (미정)", 230, y)
    draw_text(f"🎖 직급: {str(user['position'])}", 400, y)
    y -= line_height
    draw_text(f"📅 지급일: 2025-04-06", 50, y)
    y -= line_height

    # 근무 정보 (수정됨)
    work_hours = payroll.get("work_hours", 0)
    print("📌 3단계: work_hours 값 =", work_hours)  # ← 이 줄 추가!
    overtime_hours = payroll.get("overtime_hours", 0)
    hourly_wage = payroll.get("hourly_wage", 0)
    draw_text(f"⏰ 근무시간: {work_hours}시간", 50, y)
    draw_text(f"⌛ 연장근무: {overtime_hours}시간", 200, y)
    draw_text(f"💸 시급: {hourly_wage:,}원", 400, y)
    y -= line_height * 2

    # 지급 항목
    draw_center("──────────── 지급 항목 ────────────", y)
    y -= line_height
    draw_text(f"기본급           : {payroll.get('base_salary', 0):,}원", 50, y)
    draw_text(f"연장근로수당     : {payroll.get('overtime_allowance', 0):,}원", 300, y)
    y -= line_height
    draw_text(f"야간근로수당     : {payroll.get('night_allowance', 0):,}원", 50, y)
    draw_text(f"휴일근로수당     : {payroll.get('holiday_allowance', 0):,}원", 300, y)
    y -= line_height
    draw_text(f"가족수당         : {payroll.get('family_allowance', 0):,}원", 50, y)
    draw_text(f"식대             : {payroll.get('meal_allowance', 0):,}원", 300, y)
    y -= line_height * 2

    # 공제 항목
    draw_center("──────────── 공제 항목 ────────────", y)
    y -= line_height
    draw_text(f"소득세           : {payroll.get('tax', 0):,}원", 50, y)
    draw_text(f"국민연금         : {payroll.get('national_pension', 0):,}원", 300, y)
    y -= line_height
    draw_text(f"고용보험         : {payroll.get('employment_insurance', 0):,}원", 50, y)
    draw_text(f"건강보험         : {payroll.get('health_insurance', 0):,}원", 300, y)
    y -= line_height
    draw_text(f"장기요양보험     : {payroll.get('care_insurance', 0):,}원", 50, y)
    draw_text(f"노조비           : {payroll.get('union_fee', 0):,}원", 300, y)
    y -= line_height * 2

    # 하단 합계 + 실수령액 음수 표시 개선
    total_payment = payroll.get("total_payment", 0)
    total_deduction = payroll.get("total_deduction", 0)
    actual_payment = payroll.get("actual_payment", 0)

    draw_text(f"💰 지급합계  : {total_payment:,}원", 50, y)
    draw_text(f"📉 공제합계  : {total_deduction:,}원", 250, y)

    # 음수일 경우 강조
    if actual_payment < 0:
        actual_display = f"-{abs(actual_payment):,}원 ❗"
    else:
        actual_display = f"{actual_payment:,}원"

    draw_text(f"✅ 실수령액  : {actual_display}", 450, y)

    # 종료
    c.showPage()
    c.save()
    buffer.seek(0)

    with open(output_path, "wb") as f:
        f.write(buffer.read())
    buffer.close()
    return output_path
