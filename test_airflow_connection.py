import requests
import sys

def test_connections():
    print("=" * 60)
    print("Airflow DAG 연결 테스트")
    print("=" * 60)
    
    hosts = ['localhost', 'host.docker.internal']
    
    for host in hosts:
        print(f"\n[{host}] 테스트:")
        print("-" * 60)
        
        try:
            backend_url = f'http://{host}:8080/api/email-subscriptions/email-consent'
            response = requests.get(backend_url, timeout=5)
            if response.status_code == 200:
                print(f"✓ Spring Boot ({host}:8080): 연결 성공")
            else:
                print(f"✗ Spring Boot ({host}:8080): 응답 오류 {response.status_code}")
        except Exception as e:
            print(f"✗ Spring Boot ({host}:8080): 연결 실패 - {str(e)}")
        
        try:
            python_url = f'http://{host}:9000/api/health'
            response = requests.get(python_url, timeout=5)
            if response.status_code == 200:
                print(f"✓ Python API ({host}:9000): 연결 성공")
            else:
                print(f"✗ Python API ({host}:9000): 응답 오류 {response.status_code}")
        except Exception as e:
            print(f"✗ Python API ({host}:9000): 연결 실패 - {str(e)}")
    
    print("\n" + "=" * 60)
    print("권장사항:")
    print("=" * 60)
    print("1. 로컬에서 실행 중이라면 BACKEND_HOST=localhost 설정")
    print("2. Docker에서 실행 중이라면 BACKEND_HOST=host.docker.internal 설정")
    print("3. Airflow UI에서 DAG의 태스크 로그 확인")
    print("=" * 60)

if __name__ == "__main__":
    test_connections()






