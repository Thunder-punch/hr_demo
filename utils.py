# utils.py
import json
from pathlib import Path

DATA_DIR = Path("C:/Users/texcl/friend_env/hr_demo/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_user(user_data: dict):
    file_path = DATA_DIR / "users.json"
    data = []
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append(user_data)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
