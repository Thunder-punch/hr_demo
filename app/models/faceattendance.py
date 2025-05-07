"""
파일: /app/models/faceattendance.py

설치가 필요한 패키지:
----------------------------------
pip install fastapi uvicorn opencv-python face_recognition pyautogui sqlalchemy requests
pip install dlib
----------------------------------
※ dlib는 OS 및 Python 버전에 따라 사전 컴파일된 wheel 사용을 권장합니다.
"""

import os
import sys
import cv2
import face_recognition
import datetime
import pyautogui
import asyncio
import numpy as np
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

# 데이터베이스 세션과 모델 가져오기 (예시)
from database import get_db
from models import User, Attendance, UserFace  # UserFace: 여러 얼굴 이미지 저장 테이블

router = APIRouter()

# ------------------------------
# 1. 보스메인 페이지 및 얼굴 등록/다중 등록 엔드포인트
# ------------------------------
@router.get("/bossmain", response_class=HTMLResponse)
async def boss_main(request: Request):
    html_content = """
    <html>
    <head><title>Boss Main</title></head>
    <body>
      <h1>Boss Main Page</h1>
      <form action="/face/register" method="get">
        <label>단일 얼굴 등록 - 등록할 사용자 ID: <input type="number" name="user_id" value="1"></label><br>
        <button type="submit">정태우 얼굴 단일 등록</button>
      </form>
      <br>
      <form action="/face/register_all" method="get">
        <label>다중 얼굴 등록 - 등록할 사용자 ID: <input type="number" name="user_id" value="1"></label><br>
        <button type="submit">정태우 얼굴 전체 등록 (폴더 내 파일)</button>
      </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/face/register", response_class=HTMLResponse)
async def register_face_endpoint(user_id: int, db: Session = Depends(get_db)):
    """
    단일 얼굴 이미지 등록.
    노트북 카메라로 촬영하여 저장한 이미지가
    현재 파일 기준 "face" 폴더에 userID_YYYYMMDD_HHMMSS.jpg로 저장되고,
    User 테이블의 face_image_path 컬럼과 함께 UserFace 테이블에도 등록합니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 사용자")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, "face")
    os.makedirs(save_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(save_dir, f"{user_id}_{timestamp}.jpg")
    
    video_capture = cv2.VideoCapture(0)
    print("[콘솔] 카메라가 열렸습니다. 's' 키를 눌러 캡처, 'q' 키로 취소하세요.")
    captured = False
    while True:
        ret, frame = video_capture.read()
        if not ret:
            continue
        cv2.imshow('얼굴 등록 - S: 저장, Q: 취소', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            rgb_frame = frame[:, :, ::-1]
            faces = face_recognition.face_locations(rgb_frame)
            if not faces:
                print("[콘솔] 얼굴이 인식되지 않았습니다. 다시 시도해주세요.")
                continue
            cv2.imwrite(save_path, frame)
            print(f"[콘솔] 얼굴 등록 완료: {save_path}")
            captured = True
            break
        elif key == ord('q'):
            print("[콘솔] 얼굴 등록 취소")
            break
    video_capture.release()
    cv2.destroyAllWindows()
    
    if captured:
        # 단일 등록 시 User 테이블의 face_image_path 업데이트
        user.face_image_path = save_path
        db.commit()
        # 그리고 UserFace 테이블에도 새 레코드 추가
        new_face = UserFace(user_id=user_id, image_path=save_path)
        db.add(new_face)
        db.commit()
        html_content = f"""
        <html>
        <head><title>얼굴 등록 결과</title></head>
        <body>
          <h1>얼굴 등록 완료</h1>
          <p>{user.name}의 얼굴이 등록되었습니다. (파일: {save_path})</p>
          <a href="/bossmain">Boss Main으로 돌아가기</a>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    else:
        return HTMLResponse(content="<html><body><h1>얼굴 등록 취소 또는 실패</h1></body></html>")


@router.get("/face/register_all", response_class=HTMLResponse)
async def register_all_faces_endpoint(user_id: int, db: Session = Depends(get_db)):
    """
    미리 지정된 폴더("face" 폴더) 내에 있는 모든 이미지 파일(파일명이 "{user_id}_*.jpg")
    을 DB의 UserFace 테이블에 등록합니다.
    이미 등록된 이미지가 있으면 중복 등록을 방지합니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 사용자")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    face_folder = os.path.join(base_dir, "face")
    if not os.path.exists(face_folder):
        raise HTTPException(status_code=400, detail="face 폴더가 존재하지 않습니다.")
    
    count = 0
    for filename in os.listdir(face_folder):
        if filename.startswith(f"{user_id}_") and filename.endswith(".jpg"):
            image_path = os.path.join(face_folder, filename)
            # 중복 등록 확인
            exists = db.query(UserFace).filter(UserFace.user_id == user_id, UserFace.image_path == image_path).first()
            if not exists:
                new_face = UserFace(user_id=user_id, image_path=image_path)
                db.add(new_face)
                count += 1
    db.commit()
    
    html_content = f"""
    <html>
    <head><title>다중 얼굴 등록 결과</title></head>
    <body>
      <h1>다중 얼굴 등록 완료</h1>
      <p>{user.name}의 얼굴 이미지 {count}건이 등록되었습니다.</p>
      <a href="/bossmain">Boss Main으로 돌아가기</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ------------------------------
# 2. 얼굴 인식 로그인 및 출근 기록 등록 엔드포인트 (평균 임베딩 사용)
# ------------------------------
def load_registered_face_encodings(user_id: int, db: Session) -> list:
    """
    UserFace 테이블에서 해당 user_id의 모든 이미지 파일 경로를 불러와 
    얼굴 임베딩 리스트를 생성합니다.
    """
    from models import UserFace
    encodings = []
    face_records = db.query(UserFace).filter(UserFace.user_id == user_id).all()
    for record in face_records:
        if os.path.exists(record.image_path):
            image = face_recognition.load_image_file(record.image_path)
            img_encodings = face_recognition.face_encodings(image)
            if img_encodings:
                encodings.append(img_encodings[0])
    return encodings

@router.post("/face/login")
def face_login(username: str, password: str, db: Session = Depends(get_db)):
    """
    사용자 로그인 후, 노트북 카메라를 통해 얼굴 인식을 진행하고,
    등록된 모든 얼굴 이미지들의 평균 임베딩과 비교하여 인식이 성공하면
    Attendance 테이블에 clock_in 기록을 등록합니다.
    
    요청 예시 (JSON Body):
    {
       "username": "정태우",
       "password": "1234"
    }
    """
    # 간단한 인증 (실제 서비스에서는 보안 강화 필요)
    user = db.query(User).filter(User.name == username).first()
    if not user or password != "1234":
        raise HTTPException(status_code=401, detail="로그인 실패")
    
    # 다중 등록 얼굴 임베딩 로드
    known_encodings = load_registered_face_encodings(user.id, db)
    if not known_encodings:
        raise HTTPException(status_code=400, detail="등록된 얼굴 이미지에서 얼굴 인코딩 실패")
    
    # 평균 임베딩 계산
    known_avg = np.mean(known_encodings, axis=0)
    
    # 실시간 얼굴 인식
    video_capture = cv2.VideoCapture(0)
    recognized = False
    print("[콘솔] 얼굴 인식을 시작합니다. 'q' 키를 누르면 종료됩니다.")
    while True:
        ret, frame = video_capture.read()
        if not ret:
            continue
        small_frame = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
        rgb_small = small_frame[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_small)
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)
        for encoding in face_encodings:
            # 평균 임베딩과의 유클리드 거리 계산
            distance = face_recognition.face_distance([known_avg], encoding)[0]
            # tolerance 값: 0.6 (조정 가능)
            if distance < 0.6:
                recognized = True
                break
        cv2.imshow("얼굴 인식", frame)
        if recognized:
            print("[콘솔] 얼굴 인식 성공!")
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[콘솔] 얼굴 인식 취소됨.")
            break
    video_capture.release()
    cv2.destroyAllWindows()
    
    if not recognized:
        raise HTTPException(status_code=400, detail="얼굴 인식 실패")
    
    # Attendance 테이블에 clock_in 기록 등록 (현재 시간)
    now = datetime.datetime.now()
    new_attendance = Attendance(user_id=user.id, clock_in=now)
    db.add(new_attendance)
    db.commit()
    
    # 선택: pyautogui로 채팅창에 출근 메시지 전송 (채팅창 활성 상태 확인)
    now_str = now.strftime("%H:%M")
    first_message = f"{username} 현 시간 출근"
    second_message = f"{username} 출근했습니다. ({now_str})"
    pyautogui.typewrite(first_message, interval=0.05)
    pyautogui.press("enter")
    pyautogui.typewrite(second_message, interval=0.05)
    pyautogui.press("enter")
    
    return JSONResponse(content={"message": f"로그인 및 얼굴 인식 성공! 출근 기록 등록 완료 (clock_in: {now})"})

# ------------------------------
# 콘솔 모드 테스트 (웹 서버와 별도 실행 시)
# ------------------------------
def run_console_face_attendance():
    username = input("아이디: ")
    password = input("비밀번호: ")
    from database import get_db
    db = next(get_db())
    result = face_login(username, password, db)
    print(result.body.decode())

# ------------------------------
# 메인 실행 (콘솔 테스트용)
# ------------------------------
if __name__ == "__main__":
    run_console_face_attendance()
