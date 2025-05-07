# app/utils/pdf/generate_contract_pdf.py

import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 한글 폰트 경로 설정 (환경에 맞게 수정)
FONT_PATH = "C:/Users/texcl/friend_env/hr_demo/app/utils/fonts/NanumGothic.ttf"
pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH))

def generate_contract_pdf(contract_data: dict, output_path: str):
    """
    contract_data: {
        "employee_name": str,
        "employee_address": str,
        "position": str,
        "start_date": str,
        "contract_period": str,
        "salary": int,
        "working_hours": str,
        "additional_terms": str (옵션)
    }
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("NanumGothic", 12)
    width, height = A4
    y = height - 50

    # 제목: 중앙 정렬
    title = "근로계약서"
    title_width = pdfmetrics.stringWidth(title, "NanumGothic", 16)
    title_x = (width - title_width) / 2
    c.setFont("NanumGothic", 16)
    c.drawString(title_x, y, title)
    y -= 40

    # 계약 내용 입력
    c.setFont("NanumGothic", 12)
    line_height = 20
    c.drawString(50, y, f"1. 직원 성명: {contract_data.get('employee_name', '')}")
    y -= line_height
    c.drawString(50, y, f"2. 직원 주소: {contract_data.get('employee_address', '')}")
    y -= line_height
    c.drawString(50, y, f"3. 직위: {contract_data.get('position', '')}")
    y -= line_height
    c.drawString(50, y, f"4. 근로 시작일: {contract_data.get('start_date', '')}")
    y -= line_height
    c.drawString(50, y, f"5. 계약 기간: {contract_data.get('contract_period', '')}")
    y -= line_height
    c.drawString(50, y, f"6. 월 급여: {contract_data.get('salary', 0):,}원")
    y -= line_height
    c.drawString(50, y, f"7. 근무 시간: {contract_data.get('working_hours', '')}")
    y -= line_height
    if contract_data.get("additional_terms"):
        c.drawString(50, y, f"8. 추가 조건: {contract_data.get('additional_terms')}")
        y -= line_height

    # 표준 계약 조항 예시
    y -= line_height
    c.drawString(50, y, "본 계약은 상호 협의 하에 작성되었으며, 계약 조건에 동의한 후 서명함으로써 효력이 발생합니다.")
    y -= line_height * 2
    c.drawString(50, y, "회사 대표:")
    c.drawString(300, y, "직원:")
    y -= line_height * 3

    # PDF 생성 종료
    c.showPage()
    c.save()
    buffer.seek(0)
    with open(output_path, "wb") as f:
        f.write(buffer.read())
    buffer.close()
    return output_path
