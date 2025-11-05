import pymysql
import sys
from datetime import datetime, timedelta
from config.settings import settings

def check_email_subscriptions():
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            port=settings.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        print("=" * 60)
        print("이메일 구독자 목록 확인")
        print("=" * 60)
        
        cursor.execute("""
            SELECT id, name, email, is_email_consent, is_phone_consent, 
                   is_active, created_at
            FROM email_subscriptions
            ORDER BY created_at DESC
        """)
        
        subscribers = cursor.fetchall()
        
        if not subscribers:
            print("\n등록된 구독자가 없습니다.")
            return
        
        print(f"\n총 {len(subscribers)}명의 구독자가 있습니다.\n")
        print("-" * 60)
        
        email_consent_count = 0
        for sub in subscribers:
            sub_id, name, email, is_email_consent, is_phone_consent, is_active, created_at = sub
            
            consent_status = "동의" if is_email_consent else "거부"
            active_status = "활성" if is_active else "비활성"
            
            print(f"ID: {sub_id}")
            print(f"  이름: {name}")
            print(f"  이메일: {email}")
            print(f"  이메일 동의: {consent_status}")
            print(f"  전화 동의: {'동의' if is_phone_consent else '거부'}")
            print(f"  상태: {active_status}")
            print(f"  가입일: {created_at}")
            print()
            
            if is_email_consent and is_active:
                email_consent_count += 1
        
        print("-" * 60)
        print(f"이메일 발송 가능한 구독자: {email_consent_count}명")
        print("=" * 60)
        
        return email_consent_count
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()

def check_notification_logs(hours=24):
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            port=settings.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print(f"알림 발송 로그 확인 (최근 {hours}시간)")
        print("=" * 60)
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT id, user_email, symbol, notification_type, status, 
                   sent_at, error_message
            FROM notification_logs
            WHERE sent_at >= %s
            ORDER BY sent_at DESC
            LIMIT 50
        """, (cutoff_time,))
        
        logs = cursor.fetchall()
        
        if not logs:
            print(f"\n최근 {hours}시간 동안 발송된 알림이 없습니다.")
            print("\n가능한 원인:")
            print("  1. Airflow DAG가 실행되지 않았습니다.")
            print("  2. Python API 서버가 실행되지 않았습니다.")
            print("  3. 구독자가 이메일 동의를 하지 않았습니다.")
            return
        
        print(f"\n총 {len(logs)}건의 발송 로그가 있습니다.\n")
        print("-" * 60)
        
        sent_count = 0
        failed_count = 0
        pending_count = 0
        
        for log in logs:
            log_id, user_email, symbol, notification_type, status, sent_at, error_message = log
            
            status_text = "[성공]" if status == "sent" else "[실패]" if status == "failed" else "[대기]"
            
            print(f"{status_text} [{status.upper()}] {sent_at}")
            print(f"   수신자: {user_email}")
            print(f"   종목: {symbol or '전체'}")
            print(f"   유형: {notification_type}")
            if error_message:
                print(f"   오류: {error_message}")
            print()
            
            if status == "sent":
                sent_count += 1
            elif status == "failed":
                failed_count += 1
            else:
                pending_count += 1
        
        print("-" * 60)
        print(f"발송 성공: {sent_count}건")
        print(f"발송 실패: {failed_count}건")
        print(f"대기 중: {pending_count}건")
        print("=" * 60)
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def check_airflow_status():
    try:
        import requests
        
        print("\n" + "=" * 60)
        print("Airflow DAG 상태 확인")
        print("=" * 60)
        
        airflow_url = "http://localhost:8081/api/v1/dags"
        
        try:
            response = requests.get(airflow_url, timeout=5)
            if response.status_code == 200:
                print("Airflow 서버가 실행 중입니다.")
                
                dag_url = "http://localhost:8081/api/v1/dags/email_notification_dag"
                dag_response = requests.get(dag_url, timeout=5)
                
                if dag_response.status_code == 200:
                    dag_data = dag_response.json()
                    print(f"email_notification_dag가 등록되어 있습니다.")
                    
                    runs_url = f"{dag_url}/dagRuns"
                    runs_response = requests.get(runs_url, timeout=5, params={"limit": 5})
                    
                    if runs_response.status_code == 200:
                        runs_data = runs_response.json()
                        dag_runs = runs_data.get('dag_runs', [])
                        
                        if dag_runs:
                            print(f"\n최근 실행 내역 (최대 5건):")
                            print("-" * 60)
                            for run in dag_runs:
                                state = run.get('state', 'unknown')
                                start_date = run.get('start_date', 'N/A')
                                end_date = run.get('end_date', 'N/A')
                                
                                state_text = "[성공]" if state == "success" else "[실패]" if state == "failed" else "[대기]"
                                print(f"{state_text} 상태: {state}")
                                print(f"   시작: {start_date}")
                                print(f"   종료: {end_date}")
                                print()
                        else:
                            print("아직 실행된 DAG가 없습니다.")
                else:
                    print("email_notification_dag를 찾을 수 없습니다.")
            else:
                print(f"Airflow 서버 응답 오류: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("Airflow 서버에 연결할 수 없습니다.")
            print("   Airflow 서버를 시작하세요: airflow webserver --port 8081")
        except Exception as e:
            print(f"오류 발생: {e}")
            
    except ImportError:
        print("requests 라이브러리가 필요합니다. pip install requests")
    except Exception as e:
        print(f"오류 발생: {e}")

def check_python_api():
    try:
        import requests
        
        print("\n" + "=" * 60)
        print("Python API 서버 상태 확인")
        print("=" * 60)
        
        api_url = "http://localhost:9000/api/health"
        
        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                print("Python API 서버가 실행 중입니다.")
                
                email_test_url = "http://localhost:9000/api/notifications/email"
                print(f"이메일 발송 API: {email_test_url}")
            else:
                print(f"Python API 서버 응답 오류: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("Python API 서버에 연결할 수 없습니다.")
            print("   Python API 서버를 시작하세요: python start_python_api.py")
        except Exception as e:
            print(f"오류 발생: {e}")
            
    except ImportError:
        print("requests 라이브러리가 필요합니다. pip install requests")
    except Exception as e:
        print(f"오류 발생: {e}")

def check_spring_backend():
    try:
        import requests
        
        print("\n" + "=" * 60)
        print("Spring Boot 백엔드 상태 확인")
        print("=" * 60)
        
        backend_url = "http://localhost:8080/api/email-subscriptions/email-consent"
        
        try:
            response = requests.get(backend_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    subscriptions = data['data']['subscriptions']
                    print(f"Spring Boot 백엔드가 실행 중입니다.")
                    print(f"이메일 동의 구독자: {len(subscriptions)}명")
                else:
                    print("구독자 데이터를 가져올 수 없습니다.")
            else:
                print(f"Spring Boot 백엔드 응답 오류: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("Spring Boot 백엔드에 연결할 수 없습니다.")
            print("   Spring Boot 서버를 시작하세요")
        except Exception as e:
            print(f"오류 발생: {e}")
            
    except ImportError:
        print("requests 라이브러리가 필요합니다. pip install requests")
    except Exception as e:
        print(f"오류 발생: {e}")

def main():
    print("\n" + "=" * 60)
    print("이메일 구독 발송 확인 도구")
    print("=" * 60)
    print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    email_consent_count = check_email_subscriptions()
    check_notification_logs(hours=24)
    
    check_spring_backend()
    check_python_api()
    check_airflow_status()
    
    print("\n" + "=" * 60)
    print("요약 및 권장사항")
    print("=" * 60)
    
    if email_consent_count > 0:
        print(f"이메일 발송 가능한 구독자: {email_consent_count}명")
        print("\n이메일이 발송되지 않았다면:")
        print("  1. Airflow 스케줄러가 실행 중인지 확인하세요")
        print("     - airflow scheduler")
        print("  2. Python API 서버가 실행 중인지 확인하세요")
        print("     - python start_python_api.py")
        print("  3. Spring Boot 서버가 실행 중인지 확인하세요")
        print("  4. Airflow DAG를 수동으로 실행할 수 있습니다")
        print("     - Airflow UI에서 'Trigger DAG' 클릭")
    else:
        print("이메일 동의한 구독자가 없습니다.")
        print("   구독자가 이메일 동의를 했는지 확인하세요.")
    
    print("\n" + "=" * 60)

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

