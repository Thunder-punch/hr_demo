# reset_db.py
from database import engine
from models import Base

# 테이블 전부 드롭하고 재생성
print("⛔ 기존 테이블 삭제 중...")
Base.metadata.drop_all(bind=engine)

print("✅ 테이블 재생성 중...")
Base.metadata.create_all(bind=engine)

print("🎉 DB 초기화 완료!")
