# create_users.py
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, PositionEnum
from passlib.context import CryptContext
from datetime import date

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(name, email, position, base_salary):
    db: Session = SessionLocal()
    hashed_pw = pwd_context.hash("1234")
    user = User(
        name=name,
        email=email,
        phone="010-1111-2222",
        position=position,
        join_date=date(2024, 1, 1),
        password_hash=hashed_pw,
        base_salary=base_salary
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✅ 사용자 생성: {user.name} (ID: {user.id})")
    db.close()
    return user.id

if __name__ == "__main__":
    create_user("홍길동", "hong@corp.com", PositionEnum.사원, 3200000)
    create_user("정태우", "jung@corp.com", PositionEnum.사원, 3000000)
    create_user("김민지", "minji@corp.com", PositionEnum.사장, 5000000)
