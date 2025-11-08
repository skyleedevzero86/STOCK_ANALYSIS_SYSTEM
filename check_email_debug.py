import requests
import sys
import os
from datetime import datetime

def check_airflow_connection():
    """Airflow 서버 연결 확인"""
    print("=" * 60)
    print("1. Airflow 서버 연결 확인")
    print("=" * 60)
    
    try:
        airflow_url = "http://localhost:8081/api/v1/dags/email_notification_dag"
        response = requests.get(airflow_url, timeout=5)
        
        if response.status_code == 200:
            print("✓ Airflow 서버가 실행 중입니다.")
            dag_data = response.json()
            print(f"✓ email_notification_dag가 등록되어 있습니다.")
            
            # DAG 트리거 테스트
            trigger_url = f"{airflow_url}/dagRuns"
            trigger_data = {
                "dag_run_id": f"test__{datetime.now().isoformat()}",
                "conf": {}
            }
            
            try:
                trigger_response = requests.post(
                    trigger_url, 
                    json=trigger_data,
                    timeout=10,
                    auth=('airflow', 'airflow')
                )
                if trigger_response.status_code in [200, 201]:
                    print("✓ DAG 트리거 테스트 성공")
                else:
                    print(f"✗ DAG 트리거 테스트 실패: {trigger_response.status_code}")
                    print(f"  응답: {trigger_response.text[:200]}")
            except Exception as e:
                print(f"✗ DAG 트리거 테스트 실패: {str(e)}")
            
            return True
        else:
            print(f"✗ Airflow 서버 응답 오류: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Airflow 서버에 연결할 수 없습니다.")
        print("  → Airflow 서버를 시작하세요:")
        print("    - airflow webserver --port 8081")
        print("    - airflow scheduler")
        return False
    except Exception as e:
        print(f"✗ 오류 발생: {str(e)}")
        return False

def check_python_api():
    """Python API 서버 확인"""
    print("\n" + "=" * 60)
    print("2. Python API 서버 확인")
    print("=" * 60)
    
    try:
        api_url = "http://localhost:9000/api/health"
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            print("✓ Python API 서버가 실행 중입니다.")
            
            # 이메일 API 엔드포인트 확인
            email_url = "http://localhost:9000/api/notifications/email"
            
            # 테스트 요청 (실제 발송은 하지 않음)
            test_response = requests.post(
                email_url,
                params={
                    'to_email': 'test@example.com',
                    'subject': 'Test',
                    'body': 'Test'
                },
                timeout=5
            )
            
            if test_response.status_code in [200, 400]:  # 400도 정상 (설정 문제일 수 있음)
                print("✓ 이메일 API 엔드포인트가 응답합니다.")
                if test_response.status_code == 200:
                    data = test_response.json()
                    if data.get('success'):
                        print("✓ 이메일 발송 테스트 성공")
                    else:
                        print(f"✗ 이메일 발송 실패: {data.get('message', '알 수 없는 오류')}")
                else:
                    print(f"⚠ 이메일 API 응답: {test_response.status_code}")
                    print(f"  응답: {test_response.text[:200]}")
            else:
                print(f"✗ 이메일 API 응답 오류: {test_response.status_code}")
                print(f"  응답: {test_response.text[:200]}")
            
            return True
        else:
            print(f"✗ Python API 서버 응답 오류: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Python API 서버에 연결할 수 없습니다.")
        print("  → Python API 서버를 시작하세요:")
        print("    - python api_server.py")
        return False
    except Exception as e:
        print(f"✗ 오류 발생: {str(e)}")
        return False

def check_spring_backend():
    """Spring Boot 백엔드 확인"""
    print("\n" + "=" * 60)
    print("3. Spring Boot 백엔드 확인")
    print("=" * 60)
    
    try:
        backend_url = "http://localhost:8080/api/email-subscriptions/email-consent"
        response = requests.get(backend_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                subscriptions = data['data']['subscriptions']
                print(f"✓ Spring Boot 백엔드가 실행 중입니다.")
                print(f"✓ 이메일 동의 구독자: {len(subscriptions)}명")
                
                if subscriptions:
                    print("\n구독자 목록:")
                    for sub in subscriptions[:5]:
                        print(f"  - {sub.get('name', 'N/A')} ({sub.get('email', 'N/A')})")
                else:
                    print("⚠ 이메일 동의한 구독자가 없습니다.")
                    print("  → 구독 신청 시 이메일 동의를 체크해야 합니다.")
                
                return True
            else:
                print("✗ 구독자 데이터를 가져올 수 없습니다.")
                return False
        else:
            print(f"✗ Spring Boot 백엔드 응답 오류: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Spring Boot 백엔드에 연결할 수 없습니다.")
        print("  → Spring Boot 서버를 시작하세요")
        return False
    except Exception as e:
        print(f"✗ 오류 발생: {str(e)}")
        return False

def check_email_config():
    """이메일 설정 확인"""
    print("\n" + "=" * 60)
    print("4. 이메일 설정 확인")
    print("=" * 60)
    
    try:
        from config.settings import settings
        
        print(f"SMTP 서버: {settings.EMAIL_SMTP_SERVER}")
        print(f"SMTP 포트: {settings.EMAIL_SMTP_PORT}")
        print(f"이메일 사용자: {settings.EMAIL_USER}")
        print(f"이메일 비밀번호: {'*' * len(settings.EMAIL_PASSWORD) if settings.EMAIL_PASSWORD else '설정되지 않음'}")
        
        if not all([settings.EMAIL_SMTP_SERVER, settings.EMAIL_USER, settings.EMAIL_PASSWORD]):
            print("✗ 이메일 설정이 완전하지 않습니다.")
            print("  → .env 파일에 EMAIL_SMTP_SERVER, EMAIL_USER, EMAIL_PASSWORD를 설정하세요.")
            return False
        else:
            print("✓ 이메일 설정이 완료되어 있습니다.")
            return True
            
    except Exception as e:
        print(f"✗ 설정 확인 오류: {str(e)}")
        return False

def check_network_connectivity():
    """네트워크 연결 확인"""
    print("\n" + "=" * 60)
    print("5. 네트워크 연결 확인")
    print("=" * 60)
    
    hosts = [
        ('localhost:8080', 'Spring Boot'),
        ('localhost:9000', 'Python API'),
        ('localhost:8081', 'Airflow'),
        ('host.docker.internal:8080', 'Spring Boot (Docker)'),
        ('host.docker.internal:9000', 'Python API (Docker)'),
        ('host.docker.internal:8081', 'Airflow (Docker)'),
    ]
    
    for host, service in hosts:
        try:
            response = requests.get(f'http://{host}', timeout=2)
            print(f"✓ {service} ({host}): 연결 가능")
        except:
            print(f"✗ {service} ({host}): 연결 불가")

def main():
    print("\n" + "=" * 60)
    print("메일 발송 디버깅 도구")
    print("=" * 60)
    print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    results.append(("Airflow 서버", check_airflow_connection()))
    results.append(("Python API 서버", check_python_api()))
    results.append(("Spring Boot 백엔드", check_spring_backend()))
    results.append(("이메일 설정", check_email_config()))
    check_network_connectivity()
    
    print("\n" + "=" * 60)
    print("요약 및 권장사항")
    print("=" * 60)
    
    all_ok = all(result[1] for result in results)
    
    if all_ok:
        print("✓ 모든 서비스가 정상적으로 실행 중입니다.")
        print("\n메일 발송이 안 된다면:")
        print("  1. Spring Boot 로그 확인 (AirflowClient 호출 여부)")
        print("  2. Airflow 로그 확인 (DAG 실행 여부)")
        print("  3. Python API 로그 확인 (이메일 발송 시도 여부)")
    else:
        print("✗ 일부 서비스가 실행되지 않았습니다.\n")
        for service, status in results:
            status_text = "✓ 정상" if status else "✗ 문제"
            print(f"  {service}: {status_text}")
        
        print("\n권장사항:")
        print("  1. 모든 서버를 실행하세요:")
        print("     - Spring Boot: ./start_spring_boot.sh 또는 start_spring_boot.bat")
        print("     - Python API: python api_server.py")
        print("     - Airflow: airflow webserver --port 8081 & airflow scheduler")
        print("  2. 이메일 설정을 확인하세요 (.env 파일)")
        print("  3. 네트워크 연결을 확인하세요 (방화벽, Docker 네트워크 등)")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)





