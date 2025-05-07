import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

def send_salary_mail(to_email, subject, body, attachment=None):
    # .env에서 이메일 사용자명과 비밀번호 가져오기
    from_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")

    # SMTP 서버 설정 (네이버 SMTP 사용)
    smtp_server = "smtp.naver.com"
    smtp_port = 465
    smtp_ssl = True

    # 이메일 메시지 구성
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # 첨부 파일이 있을 경우
    if attachment:
        abs_pdf_path = os.path.abspath(attachment)
        print(f"첨부 파일 경로: {abs_pdf_path}")

        if abs_pdf_path.lower().endswith('.pdf'):
            print("PDF 파일로 확인됨")
            try:
                with open(abs_pdf_path, "rb") as file:
                    print("파일 열기 성공")
                    part = MIMEBase('application', 'pdf')
                    part.set_payload(file.read())
                    encoders.encode_base64(part)

                    # ✅ 파일명은 고정 (영문): 'payroll.pdf'
                    part.add_header(
                        'Content-Disposition',
                        'attachment; filename="payroll.pdf"'
                    )
                    part.add_header(
                        'Content-Type',
                        'application/pdf'
                    )

                    msg.attach(part)
                    print("PDF 파일 첨부 성공")
            except Exception as e:
                print(f"PDF 파일 첨부 실패: {e}")
                return False
        else:
            print(f"첨부된 파일은 PDF 형식이 아닙니다. 파일 확장자: {abs_pdf_path.split('.')[-1]}")
            return False

    # 이메일 전송
    try:
        if smtp_ssl:
            print("SMTP SSL 연결 시도")
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            print("SMTP TLS 연결 시도")
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()

        print(f"로그인 시도: {from_email}")
        server.login(from_email, password)
        print(f"이메일 전송 시도: {to_email}")
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(f"이메일 전송 성공: {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"이메일 인증 실패: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"서버 연결 실패: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"일반 이메일 전송 오류: {e}")
        return False
    except Exception as e:
        print(f"이메일 전송 실패: {e}")
        return False
