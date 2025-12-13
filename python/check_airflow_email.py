import sys
import os
import requests
from datetime import datetime

def check_python_api():
    print("=" * 60)
    print("1. Python API 서버 확인")
    print("=" * 60)
    
    hosts = ['localhost', 'host.docker.internal']
    ports = [9000, 8001]
    
    for host in hosts:
        for port in ports:
            try:
                url = f"http://{host}:{port}/docs"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"[OK] Python API 서버 실행 중: {host}:{port}")
                    
                    try:
                        test_url = f"http://{host}:{port}/api/notifications/email"
                        test_response = requests.post(
                            test_url,
                            params={'to_email': 'test@test.com', 'subject': 'test', 'body': 'test'},
                            timeout=5
                        )
                        print(f"  - 이메일 엔드포인트 응답: {test_response.status_code}")
                    except Exception as e:
                        print(f"  - 이메일 엔드포인트 테스트 실패: {str(e)}")
                    
                    return host, port
            except Exception as e:
                print(f"[FAIL] {host}:{port} 연결 실패: {str(e)}")
    
    print("[ERROR] Python API 서버를 찾을 수 없습니다.")
    return None, None

def check_spring_boot():
    print("\n" + "=" * 60)
    print("2. Spring Boot 서버 확인")
    print("=" * 60)
    
    hosts = ['localhost', 'host.docker.internal']
    port = 8080
    
    for host in hosts:
        try:
            url = f"http://{host}:{port}/api/email-subscriptions/email-consent"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[OK] Spring Boot 서버 실행 중: {host}:{port}")
                return host
            else:
                print(f"[WARNING] {host}:{port} 응답 코드: {response.status_code}")
        except Exception as e:
            print(f"[FAIL] {host}:{port} 연결 실패: {str(e)}")
    
    print("[ERROR] Spring Boot 서버를 찾을 수 없습니다.")
    return None

def check_subscribers(backend_host):
    print("\n" + "=" * 60)
    print("3. 구독자 확인")
    print("=" * 60)
    
    try:
        url = f"http://{backend_host}:8080/api/email-subscriptions/email-consent"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                subscriptions = data['data']['subscriptions']
                print(f"[OK] 구독자 수: {len(subscriptions)}명")
                
                email_consent_count = 0
                for sub in subscriptions:
                    if sub.get('isEmailConsent', False):
                        email_consent_count += 1
                        print(f"  - {sub.get('name', 'N/A')} ({sub.get('email', 'N/A')})")
                
                print(f"\n이메일 동의 구독자: {email_consent_count}명")
                return subscriptions
            else:
                print("[WARNING] 구독자 데이터 조회 실패")
                return []
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"[ERROR] 구독자 조회 실패: {str(e)}")
        return []

def check_analysis_data(python_host, python_port):
    print("\n" + "=" * 60)
    print("4. 주식 분석 데이터 확인")
    print("=" * 60)
    
    try:
        url = f"http://{python_host}:{python_port}/api/analysis/all"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 분석 데이터 조회 성공: {len(data)}개 종목")
            
            valid_stocks = [s for s in data if s.get('currentPrice', 0) > 0]
            print(f"  - 유효한 데이터: {len(valid_stocks)}개")
            
            if valid_stocks:
                for stock in valid_stocks[:3]:
                    symbol = stock.get('symbol', 'N/A')
                    price = stock.get('currentPrice', 0)
                    print(f"  - {symbol}: ${price:.2f}")
            
            return data
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"  응답: {response.text[:200]}")
            return []
    except Exception as e:
        print(f"[ERROR] 분석 데이터 조회 실패: {str(e)}")
        return []

def check_email_config():
    print("\n" + "=" * 60)
    print("5. 이메일 설정 확인")
    print("=" * 60)
    
    from config.settings import get_settings
    settings = get_settings()
    
    smtp_server = settings.EMAIL_SMTP_SERVER
    smtp_port = settings.EMAIL_SMTP_PORT
    user = settings.EMAIL_USER
    password = settings.EMAIL_PASSWORD
    
    print(f"SMTP 서버: {smtp_server}")
    print(f"SMTP 포트: {smtp_port}")
    print(f"이메일 사용자: {user}")
    print(f"비밀번호: {'설정됨' if password else '설정되지 않음'}")
    
    if all([smtp_server, user, password]):
        print("[OK] 이메일 설정이 완료되었습니다.")
        return True
    else:
        missing = []
        if not smtp_server:
            missing.append("EMAIL_SMTP_SERVER")
        if not user:
            missing.append("EMAIL_USER")
        if not password:
            missing.append("EMAIL_PASSWORD")
        print(f"[ERROR] 다음 환경 변수가 필요합니다: {', '.join(missing)}")
        return False

def test_email_send(python_host, python_port, test_email):
    print("\n" + "=" * 60)
    print("6. 이메일 발송 테스트")
    print("=" * 60)
    
    if not test_email:
        print("[SKIP] 테스트 이메일 주소가 제공되지 않았습니다.")
        return None
    
    try:
        url = f"http://{python_host}:{python_port}/api/notifications/email"
        response = requests.post(
            url,
            params={
                'to_email': test_email,
                'subject': f'Airflow 테스트 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                'body': '이것은 Airflow 이메일 발송 테스트입니다.'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"[OK] 이메일 발송 성공: {test_email}")
                return True
            else:
                print(f"[FAIL] 이메일 발송 실패: {data.get('message', '알 수 없는 오류')}")
                return False
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"  응답: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[ERROR] 이메일 발송 테스트 실패: {str(e)}")
        return False

def main():
    print("\n" + "=" * 60)
    print("Airflow 이메일 발송 진단 도구")
    print("=" * 60 + "\n")
    
    python_host, python_port = check_python_api()
    if not python_host:
        print("\n[ERROR] Python API 서버가 실행 중이지 않습니다.")
        print("  해결 방법:")
        print("  1. Python API 서버를 실행하세요:")
        print("     python start_python_api.py")
        print("     또는")
        print("     python api_server_enhanced.py")
        sys.exit(1)
    
    backend_host = check_spring_boot()
    if not backend_host:
        print("\n[WARNING] Spring Boot 서버가 실행 중이지 않습니다.")
        print("  구독자 목록을 조회할 수 없습니다.")
    
    subscribers = []
    if backend_host:
        subscribers = check_subscribers(backend_host)
        if not subscribers:
            print("\n[WARNING] 구독자가 없습니다.")
            print("  이메일 구독 페이지에서 구독자를 등록하세요.")
    
    analysis_data = check_analysis_data(python_host, python_port)
    if not analysis_data:
        print("\n[WARNING] 분석 데이터가 없습니다.")
        print("  Python API 서버가 주식 데이터를 수집하지 못하고 있습니다.")
    
    email_config_ok = check_email_config()
    if not email_config_ok:
        print("\n[ERROR] 이메일 설정이 완전하지 않습니다.")
        print("  환경 변수를 설정하세요.")
    
    print("\n" + "=" * 60)
    print("진단 요약")
    print("=" * 60)
    
    issues = []
    if not python_host:
        issues.append("Python API 서버가 실행 중이지 않음")
    if not backend_host:
        issues.append("Spring Boot 서버가 실행 중이지 않음")
    if not subscribers:
        issues.append("구독자가 없음")
    if not analysis_data:
        issues.append("분석 데이터가 없음")
    if not email_config_ok:
        issues.append("이메일 설정이 완전하지 않음")
    
    if issues:
        print("\n[문제점]")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n[해결 방법]")
        print("  1. 모든 서버가 실행 중인지 확인:")
        print("     - Python API: http://localhost:9000 또는 http://localhost:8001")
        print("     - Spring Boot: http://localhost:8080")
        print("     - Airflow: http://localhost:8081")
        print("  2. 환경 변수 확인:")
        print("     - EMAIL_SMTP_SERVER")
        print("     - EMAIL_USER")
        print("     - EMAIL_PASSWORD")
        print("  3. Airflow DAG 로그 확인:")
        print("     - Airflow UI에서 'email_notification_dag' 실행 로그 확인")
        print("  4. 구독자 등록 확인:")
        print("     - http://localhost:8080/email-subscription.html")
    else:
        print("\n[OK] 모든 항목이 정상입니다.")
        print("  Airflow DAG가 정상적으로 실행되어야 합니다.")
    
    print("\n" + "=" * 60)
    
    test_email = input("\n테스트 이메일 주소를 입력하세요 (Enter로 건너뛰기): ").strip()
    if test_email:
        test_email_send(python_host, python_port, test_email)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

