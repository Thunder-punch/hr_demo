# hr_demo/app/utils/logger.py

import os
import logging
import traceback
from datetime import datetime
from pathlib import Path

# ✅ 로그 저장 경로 설정
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)  # 경로 없으면 생성

# ✅ 오늘 날짜 기반 로그 파일 이름
today = datetime.now().strftime("%Y-%m-%d")
log_path = log_dir / f"app_{today}.log"

# ✅ 로깅 설정
logging.basicConfig(
    filename=log_path,
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    encoding="utf-8"
)

def log(msg: str, tag: str = "APP"):
    line = f"[{tag}] {msg}"
    print(f"🔍 {line}")
    logging.info(line)

def print_exception():
    print("❌ 예외 발생 로그 ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓")
    traceback.print_exc()
    print("❌ ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑")
    logging.error("❌ 예외 발생", exc_info=True)
