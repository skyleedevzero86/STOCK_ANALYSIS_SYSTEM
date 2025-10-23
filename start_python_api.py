import subprocess
import sys
import os
import time

def start_python_api():
    print("Python API 서버를 시작합니다...")
    print("포트: 9000")
    print("종료하려면 Ctrl+C를 누르세요")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "api_server.py"
        ])
    except KeyboardInterrupt:
        print("\nPython API 서버가 종료되었습니다.")
    except Exception as e:
        print(f"Python API 서버 실행 중 오류: {str(e)}")

if __name__ == "__main__":
    start_python_api()
