import subprocess
import time
import os

HR_PROJECT_PATH = "C:/Users/texcl/friend_env/hr_demo"
FRONTEND_PATH = os.path.join(HR_PROJECT_PATH, "frontend")
OLLAMA_PATH = "C:/Users/texcl/AppData/Local/Programs/Ollama"

def run_ollama():
    print("✅ 인사과장A 서버 실행 중... (http://localhost:11434)")
    return subprocess.Popen(
        ['ollama', 'serve'],
        cwd=OLLAMA_PATH,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def run_backend():
    print("✅ 백엔드 서버 실행 중... (http://localhost:8000)")
    return subprocess.Popen(
        ['uvicorn', 'main:app', '--reload', '--host', '127.0.0.1'],
        cwd=HR_PROJECT_PATH
    )

def run_frontend():
    print("✅ 프론트엔드 앱 실행 중... (http://localhost:3000)")
    return subprocess.Popen(
        ['cmd', '/c', 'npm start'],
        cwd=FRONTEND_PATH
    )

def main():
    print("🚀 인사과장A 시스템 시작 중...")

    ollama_process = run_ollama()
    time.sleep(5)

    backend_process = run_backend()
    time.sleep(5)

    frontend_process = run_frontend()

    print("\n🌐 브라우저를 열려면 http://localhost:3000 으로 접속하세요.")

    try:
        backend_process.wait()
        frontend_process.wait()
        ollama_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 실행 중단: 서버 종료 중...")
        backend_process.terminate()
        frontend_process.terminate()
        ollama_process.terminate()

if __name__ == '__main__':
    main()
