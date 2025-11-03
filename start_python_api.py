import subprocess
import sys
import os
import time
import socket

def check_port_available(port):
    """포트가 사용 가능한지 확인"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def start_python_api():
    print("=" * 60)
    print("Python API 서버 시작")
    print("=" * 60)
    print("포트: 9000")
    print("API 엔드포인트: http://localhost:9000")
    print("문서: http://localhost:9000/docs")
    print("-" * 60)
    
    if not check_port_available(9000):
        print("  경고: 포트 9000이 이미 사용 중입니다.")
        print("   다른 프로세스가 실행 중인지 확인하세요.")
        response = input("   계속 진행하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            print("서버 시작이 취소되었습니다.")
            return
    
    print("\n서버를 시작합니다...")
    print("종료하려면 Ctrl+C를 누르세요")
    print("-" * 60)
    print()
    
    try:

        subprocess.run([
            sys.executable, "-m", "uvicorn", "api_server:app",
            "--host", "0.0.0.0",
            "--port", "9000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n" + "-" * 60)
        print("Python API 서버가 종료되었습니다.")
        print("-" * 60)
    except FileNotFoundError:
        print(" 오류: uvicorn을 찾을 수 없습니다.")
        print("   다음 명령으로 설치하세요: pip install uvicorn[standard]")
        print("\n또는 직접 실행:")
        print("   python api_server.py")
    except Exception as e:
        print(f" Python API 서버 실행 중 오류: {str(e)}")
        print("\n대안: 다음 명령으로 직접 실행할 수 있습니다:")
        print("   python api_server.py")

if __name__ == "__main__":
    start_python_api()
