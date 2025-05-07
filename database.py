# C:\Users\texcl\friend_env\hr_demo\database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()

# 각각 개별 항목으로 가져오기
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# PostgreSQL 연결 문자열 생성
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 생성기 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 선언적 기반 클래스 (모델 정의 시 사용)
Base = declarative_base()

# DB 세션 연결 함수 (FastAPI 의 Depends로 사용)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
