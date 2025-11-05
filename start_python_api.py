import subprocess
import sys
import os
import time
import socket
import signal
import atexit

airflow_process = None
api_process = None

def cleanup_processes():
    global airflow_process, api_process
    if airflow_process:
        try:
            airflow_process.terminate()
            airflow_process.wait(timeout=5)
        except:
            try:
                airflow_process.kill()
            except:
                pass
    if api_process:
        try:
            api_process.terminate()
            api_process.wait(timeout=5)
        except:
            try:
                api_process.kill()
            except:
                pass

def signal_handler(sig, frame):
    cleanup_processes()
    sys.exit(0)

def check_port_available(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def start_airflow_scheduler():
    global airflow_process
    try:
        airflow_process = subprocess.Popen(
            ["airflow", "scheduler"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        print("Airflow 스케줄러 시작됨")
        return True
    except FileNotFoundError:
        print("경고: airflow 명령을 찾을 수 없습니다.")
        print("  Airflow가 설치되어 있는지 확인하세요.")
        return False
    except Exception as e:
        print(f"Airflow 스케줄러 시작 실패: {str(e)}")
        return False

def start_python_api():
    global api_process
    print("=" * 60)
    print("Python API 서버 및 Airflow 스케줄러 시작")
    print("=" * 60)
    print("포트: 9000")
    print("API 엔드포인트: http://localhost:9000")
    print("문서: http://localhost:9000/docs")
    print("Airflow UI: http://localhost:8081")
    print("-" * 60)
    
    if not check_port_available(9000):
        print("  경고: 포트 9000이 이미 사용 중입니다.")
        print("   다른 프로세스가 실행 중인지 확인하세요.")
        response = input("   계속 진행하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            print("서버 시작이 취소되었습니다.")
            return
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_processes)
    
    airflow_started = start_airflow_scheduler()
    if airflow_started:
        time.sleep(2)
    
    print("\n서버를 시작합니다...")
    print("종료하려면 Ctrl+C를 누르세요")
    print("-" * 60)
    print()
    
    try:
        api_process = subprocess.run([
            sys.executable, "-m", "uvicorn", "api_server:app",
            "--host", "0.0.0.0",
            "--port", "9000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n" + "-" * 60)
        print("서버가 종료되었습니다.")
        print("-" * 60)
        cleanup_processes()
    except FileNotFoundError:
        print(" 오류: uvicorn을 찾을 수 없습니다.")
        print("   다음 명령으로 설치하세요: pip install uvicorn[standard]")
        print("\n또는 직접 실행:")
        print("   python api_server.py")
        cleanup_processes()
    except Exception as e:
        print(f" Python API 서버 실행 중 오류: {str(e)}")
        print("\n대안: 다음 명령으로 직접 실행할 수 있습니다:")
        print("   python api_server.py")
        cleanup_processes()

if __name__ == "__main__":
    start_python_api()
