import requests
import sys
from datetime import datetime

def check_subscribers():
    try:
        print("=" * 60)
        print("이메일 구독자 확인")
        print("=" * 60)
        
        url = "http://localhost:8080/api/email-subscriptions/email-consent"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                subscriptions = data['data']['subscriptions']
                print(f"\n총 {len(subscriptions)}명의 이메일 동의 구독자가 있습니다.\n")
                
                for sub in subscriptions:
                    print(f"이름: {sub.get('name', 'N/A')}")
                    print(f"이메일: {sub.get('email', 'N/A')}")
                    print(f"가입일: {sub.get('createdAt', 'N/A')}")
                    print("-" * 60)
                
                return len(subscriptions)
            else:
                print("구독자 데이터를 가져올 수 없습니다.")
                return 0
        else:
            print(f"서버 응답 오류: {response.status_code}")
            print(f"   응답: {response.text[:200]}")
            return 0
            
    except requests.exceptions.ConnectionError:
        print("Spring Boot 서버에 연결할 수 없습니다.")
        print("   서버를 시작하세요: ./start_spring_boot.sh 또는 start_spring_boot.bat")
        return 0
    except Exception as e:
        print(f"오류 발생: {e}")
        return 0

def check_python_api():
    try:
        print("\n" + "=" * 60)
        print("Python API 서버 확인")
        print("=" * 60)
        
        url = "http://localhost:9000/api/health"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print("Python API 서버가 실행 중입니다.")
            return True
        else:
            print(f"Python API 서버 응답 오류: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Python API 서버에 연결할 수 없습니다.")
        print("   서버를 시작하세요: python start_python_api.py")
        return False
    except Exception as e:
        print(f"오류 발생: {e}")
        return False

def check_airflow_dag():
    try:
        print("\n" + "=" * 60)
        print("Airflow DAG 확인")
        print("=" * 60)
        
        url = "http://localhost:8080/api/v1/dags/email_notification_dag"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            dag_data = response.json()
            print("email_notification_dag가 등록되어 있습니다.")
            
            runs_url = f"{url}/dagRuns"
            runs_response = requests.get(runs_url, timeout=5, params={"limit": 3})
            
            if runs_response.status_code == 200:
                runs_data = runs_response.json()
                dag_runs = runs_data.get('dag_runs', [])
                
                if dag_runs:
                    print(f"\n최근 실행 내역:")
                    print("-" * 60)
                    for run in dag_runs:
                        state = run.get('state', 'unknown')
                        start_date = run.get('start_date', 'N/A')
                        
                        state_text = "[성공]" if state == "success" else "[실패]" if state == "failed" else "[대기]"
                        print(f"{state_text} 상태: {state} | 시작: {start_date}")
                else:
                    print("아직 실행된 DAG가 없습니다.")
            
            return True
        else:
            print("email_notification_dag를 찾을 수 없습니다.")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Airflow 서버에 연결할 수 없습니다.")
        print("   Airflow 서버를 시작하세요: airflow webserver --port 8080")
        return False
    except Exception as e:
        print(f"오류 발생: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("이메일 구독 발송 간단 확인")
    print("=" * 60)
    print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    subscriber_count = check_subscribers()
    python_api_ok = check_python_api()
    airflow_ok = check_airflow_dag()
    
    print("\n" + "=" * 60)
    print("요약")
    print("=" * 60)
    
    if subscriber_count > 0:
        print(f"이메일 동의 구독자: {subscriber_count}명")
    else:
        print("이메일 동의 구독자가 없습니다.")
    
    if python_api_ok:
        print("Python API 서버: 실행 중")
    else:
        print("Python API 서버: 실행 안 됨")
    
    if airflow_ok:
        print("Airflow DAG: 등록됨")
    else:
        print("Airflow DAG: 확인 불가")
    
    print("\n" + "=" * 60)
    print("이메일이 발송되지 않았다면:")
    print("=" * 60)
    print("1. 모든 서버가 실행 중인지 확인:")
    print("   - Spring Boot: http://localhost:8080")
    print("   - Python API: http://localhost:9000")
    print("   - Airflow: http://localhost:8080 (Airflow UI)")
    print()
    print("2. Airflow 스케줄러 실행:")
    print("   airflow scheduler")
    print()
    print("3. Airflow DAG를 수동으로 실행:")
    print("   - Airflow UI에서 'email_notification_dag' 선택")
    print("   - 'Trigger DAG' 버튼 클릭")
    print()
    print("4. 구독자가 이메일 동의를 했는지 확인:")
    print("   http://localhost:8080/email-subscription.html")
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

