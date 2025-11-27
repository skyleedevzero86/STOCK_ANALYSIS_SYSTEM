import subprocess
import sys
import os
import time
import socket
import signal
import atexit
import threading
import http.client
import urllib.parse

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

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
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result != 0
    except Exception as e:
        print(f"포트 확인 중 오류: {e}")
        return True

def check_server_health(base_url, max_retries=10, retry_delay=1):
    for i in range(max_retries):
        try:
            parsed = urllib.parse.urlparse(base_url)
            conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=2)
            conn.request("GET", "/api/health")
            response = conn.getresponse()
            if response.status == 200:
                conn.close()
                return True
            conn.close()
        except Exception:
            pass
        time.sleep(retry_delay)
    return False

def read_output(pipe, prefix=""):
    try:
        for line in iter(pipe.readline, ''):
            if line:
                print(f"{prefix}{line.rstrip()}")
        pipe.close()
    except Exception as e:
        print(f"출력 읽기 오류: {e}")  

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
        print("경고: 포트 9000이 이미 사용 중입니다.")
        print("   다른 프로세스가 실행 중인지 확인하세요.")
        print("   Windows에서 포트를 사용하는 프로세스 확인:")
        print("     netstat -ano | findstr :9000")
        print("   또는 PowerShell에서:")
        print("     Get-NetTCPConnection -LocalPort 9000")
        print()
        try:
            response = input("   계속 진행하시겠습니까? (y/n): ")
            if response.lower() != 'y':
                print("서버 시작이 취소되었습니다.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n서버 시작이 취소되었습니다.")
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
        import platform
        is_windows = platform.system() == 'Windows'
        reload_flag = [] if is_windows else ["--reload"]
        
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if is_windows else 0
        
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api_server_enhanced:app",
             "--host", "0.0.0.0",
             "--port", "9000"] + reload_flag,
            creationflags=creation_flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        output_thread = threading.Thread(
            target=read_output,
            args=(api_process.stdout, "[API] "),
            daemon=True
        )
        output_thread.start()
        
        print(f"Python API 서버 프로세스 시작됨 (PID: {api_process.pid})")
        print("서버가 시작되는 동안 잠시 기다립니다...")
        
        base_url = "http://localhost:9000"
        if check_server_health(base_url, max_retries=15, retry_delay=1):
            print("-" * 60)
            print(f"Python API 서버가 정상적으로 시작되었습니다!")
            print(f"서버 URL: {base_url}")
            print(f"API 문서: {base_url}/docs")
            print(f"헬스 체크: {base_url}/api/health")
            print("-" * 60)
            print("서버가 실행 중입니다. 종료하려면 Ctrl+C를 누르세요.")
            print("-" * 60)
        else:
            print("-" * 60)
            print("경고: 서버 프로세스는 시작되었지만 헬스 체크에 실패했습니다.")
            print("위의 에러 메시지를 확인하세요.")
            print("-" * 60)
            if api_process.poll() is not None:
                print(f"서버 프로세스가 종료되었습니다 (종료 코드: {api_process.returncode})")
                print("에러 메시지를 확인하세요.")
                cleanup_processes()
                sys.exit(1)
        
        try:
            api_process.wait()
        except KeyboardInterrupt:
            print("\n" + "-" * 60)
            print("서버 종료 중...")
            print("-" * 60)
            cleanup_processes()
            
    except FileNotFoundError:
        print("오류: uvicorn을 찾을 수 없습니다.")
        print("   다음 명령으로 설치하세요:")
        print("   pip install uvicorn[standard]")
        print("\n또는 직접 실행:")
        print("   python api_server_enhanced.py")
        cleanup_processes()
        sys.exit(1)
    except Exception as e:
        print(f"Python API 서버 실행 중 오류: {str(e)}")
        print("\n대안: 다음 명령으로 직접 실행할 수 있습니다:")
        print("   python api_server_enhanced.py")
        print("\n또는 uvicorn을 직접 사용:")
        print("   uvicorn api_server_enhanced:app --host 0.0.0.0 --port 9000")
        cleanup_processes()
        sys.exit(1)

if __name__ == "__main__":
    start_python_api()
