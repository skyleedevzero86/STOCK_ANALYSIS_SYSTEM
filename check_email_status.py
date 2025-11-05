import requests
import sys
from datetime import datetime

def check_email_sending_status():
    print("=" * 60)
    print("이메일 발송 상태 확인")
    print("=" * 60)
    print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("1. Python API 서버 상태:")
    try:
        response = requests.get("http://localhost:9000/api/health", timeout=5)
        if response.status_code == 200:
            print("   Python API 서버: 실행 중")
        else:
            print(f"   Python API 서버: 응답 오류 ({response.status_code})")
    except:
        print("   Python API 서버: 연결 불가")
    
    print("\n2. 이메일 발송 가능 여부 확인:")
    print("   - Python API 서버가 실행 중이면 이메일 발송 API를 사용할 수 있습니다")
    print("   - 실제 발송은 Airflow DAG가 실행되어야 합니다")
    
    print("\n3. 발송 여부 확인 방법:")
    print("   방법 1: 데이터베이스에서 직접 확인")
    print("   mysql -u root -p stock_analysis")
    print("   SELECT * FROM notification_logs ORDER BY sent_at DESC LIMIT 10;")
    print()
    print("   방법 2: Spring Boot 서버에서 확인")
    print("   - http://localhost:8080/admin-dashboard.html 접속")
    print("   - 관리자 로그인 후 발송 로그 확인")
    print()
    print("   방법 3: Airflow UI에서 확인")
    print("   - http://localhost:8080 접속 (Airflow UI)")
    print("   - email_notification_dag 실행 상태 확인")
    
    print("\n4. 이메일이 발송되지 않았다면:")
    print("   - Airflow 스케줄러가 실행 중인지 확인: airflow scheduler")
    print("   - Airflow DAG를 수동 실행: Airflow UI에서 'Trigger DAG' 클릭")
    print("   - 구독자가 이메일 동의를 했는지 확인")
    print("   - Python API 서버가 실행 중인지 확인")
    
    print("\n" + "=" * 60)
    print("빠른 확인: MySQL에서 직접 확인")
    print("=" * 60)
    print("다음 SQL 쿼리를 실행하세요:")
    print()
    print("SELECT ")
    print("    user_email,")
    print("    symbol,")
    print("    notification_type,")
    print("    status,")
    print("    sent_at,")
    print("    error_message")
    print("FROM notification_logs")
    print("ORDER BY sent_at DESC")
    print("LIMIT 10;")
    print()
    print("또는 구독자 목록 확인:")
    print()
    print("SELECT ")
    print("    name,")
    print("    email,")
    print("    is_email_consent,")
    print("    is_active,")
    print("    created_at")
    print("FROM email_subscriptions")
    print("WHERE is_email_consent = TRUE")
    print("  AND is_active = TRUE;")
    print("=" * 60)

if __name__ == "__main__":
    try:
        check_email_sending_status()
    except KeyboardInterrupt:
        print("\n\n중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

