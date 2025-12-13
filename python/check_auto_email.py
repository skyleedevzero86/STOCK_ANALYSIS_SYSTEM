import sys
import os
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_all_conditions():
    print("=" * 80)
    print("자동 메일 발송 가능 여부 종합 분석")
    print("=" * 80)
    print()
    
    conditions = {
        "DAG 설정": False,
        "구독자 존재": False,
        "이메일 동의": False,
        "백엔드 API": False,
        "Python API": False,
        "분석 데이터": False,
        "이메일 설정": False
    }
    
    issues = []
    recommendations = []
    
    print("[1] DAG 설정 확인")
    print("-" * 80)
    dag_file = os.path.join(os.path.dirname(__file__), "airflow_dags", "email_notification_dag.py")
    if os.path.exists(dag_file):
        with open(dag_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "schedule='*/1 * * * *'" in content or "schedule=*/1 * * * *" in content:
                print("  [OK] DAG 스케줄: 매 1분마다 실행")
                conditions["DAG 설정"] = True
            else:
                print("  [WARNING] DAG 스케줄 설정을 확인할 수 없습니다")
                issues.append("DAG 스케줄 설정 확인 필요")
            
            if "send_daily_analysis_emails" in content:
                print("  [OK] 일일 분석 이메일 발송 함수 존재")
            else:
                print("  [WARNING] 일일 분석 이메일 발송 함수를 찾을 수 없습니다")
                issues.append("이메일 발송 함수 확인 필요")
    else:
        print("  [ERROR] DAG 파일을 찾을 수 없습니다")
        issues.append("DAG 파일이 없습니다")
    
    print()
    print("[2] 구독자 확인")
    print("-" * 80)
    backend_host = os.getenv('BACKEND_HOST', 'localhost')
    try:
        response = requests.get(
            f'http://{backend_host}:8080/api/email-subscriptions/email-consent',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                subscriptions = data['data']['subscriptions']
                email_consent_count = len([s for s in subscriptions if s.get('isEmailConsent', False)])
                
                if len(subscriptions) > 0:
                    print(f"  [OK] 구독자: {len(subscriptions)}명")
                    conditions["구독자 존재"] = True
                else:
                    print("  [WARNING] 구독자가 없습니다")
                    issues.append("구독자가 없습니다")
                
                if email_consent_count > 0:
                    print(f"  [OK] 이메일 동의 구독자: {email_consent_count}명")
                    conditions["이메일 동의"] = True
                else:
                    print("  [WARNING] 이메일 동의한 구독자가 없습니다")
                    issues.append("이메일 동의한 구독자가 없습니다")
            else:
                print(f"  [ERROR] API 응답 실패: {response.status_code}")
                issues.append("백엔드 API 응답 실패")
        else:
            print(f"  [ERROR] HTTP {response.status_code}")
            issues.append("백엔드 API 연결 실패")
    except Exception as e:
        print(f"  [ERROR] 백엔드 API 연결 실패: {str(e)}")
        issues.append("백엔드 API 서버가 실행되지 않음")
        recommendations.append("Spring Boot 백엔드 서버를 실행하세요")
    
    print()
    print("[3] 백엔드 API 상태")
    print("-" * 80)
    try:
        response = requests.get(f'http://{backend_host}:8080/api/email-subscriptions/email-consent', timeout=5)
        if response.status_code == 200:
            print("  [OK] 백엔드 API 서버 정상 작동")
            conditions["백엔드 API"] = True
        else:
            print(f"  [WARNING] 백엔드 API 응답 코드: {response.status_code}")
    except:
        print("  [ERROR] 백엔드 API 서버 연결 실패")
    
    print()
    print("[4] Python API 상태")
    print("-" * 80)
    python_api_host = os.getenv('PYTHON_API_HOST', 'localhost')
    python_api_port = os.getenv('PYTHON_API_PORT', '8001')
    ports_to_try = [python_api_port, '9000', '8001']
    python_api_ok = False
    working_port = None
    
    for port in ports_to_try:
        try:
            response = requests.get(f'http://{python_api_host}:{port}/docs', timeout=5)
            if response.status_code == 200:
                print(f"  [OK] Python API 서버 정상 작동 ({python_api_host}:{port})")
                conditions["Python API"] = True
                python_api_ok = True
                working_port = port
                break
        except:
            continue
    
    if not python_api_ok:
        print("  [ERROR] Python API 서버를 찾을 수 없습니다")
        issues.append("Python API 서버가 실행되지 않음")
        recommendations.append("Python API 서버를 실행하세요: python start_python_api.py")
    
    print()
    print("[5] 분석 데이터 확인")
    print("-" * 80)
    if python_api_ok and working_port:
        try:
            response = requests.get(
                f'http://{python_api_host}:{working_port}/api/analysis/all',
                timeout=30,
                headers={'Accept': 'application/json'}
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        valid_stocks = [s for s in data if s.get('currentPrice', 0) > 0]
                        if valid_stocks:
                            print(f"  [OK] 분석 데이터: {len(valid_stocks)}개 종목")
                            conditions["분석 데이터"] = True
                        else:
                            print(f"  [WARNING] 분석 데이터는 있지만 유효한 가격 데이터가 없습니다: {len(data)}개")
                            issues.append("유효한 분석 데이터가 없음")
                    else:
                        print("  [WARNING] 분석 데이터가 비어있습니다")
                        issues.append("분석 데이터가 비어있음")
                except ValueError:
                    print(f"  [ERROR] JSON 파싱 실패 (응답 길이: {len(response.text)} bytes)")
                    print(f"  응답 시작: {response.text[:200]}")
                    issues.append("분석 데이터 API가 JSON을 반환하지 않음")
            else:
                print(f"  [ERROR] HTTP {response.status_code}")
                issues.append("분석 데이터 조회 실패")
        except Exception as e:
            print(f"  [ERROR] 분석 데이터 조회 실패: {str(e)}")
            issues.append("분석 데이터 조회 실패")
    else:
        print("  [SKIP] Python API 서버가 실행되지 않아 확인 불가")
    
    print()
    print("[6] 이메일 설정 확인")
    print("-" * 80)
    try:
        from config.settings import get_settings
        settings = get_settings()
        smtp_server = settings.EMAIL_SMTP_SERVER
        user = settings.EMAIL_USER
        password = settings.EMAIL_PASSWORD
        
        if all([smtp_server, user, password]):
            print("  [OK] 이메일 설정 완료")
            conditions["이메일 설정"] = True
        else:
            missing = []
            if not smtp_server:
                missing.append("EMAIL_SMTP_SERVER")
            if not user:
                missing.append("EMAIL_USER")
            if not password:
                missing.append("EMAIL_PASSWORD")
            print(f"  [WARNING] 이메일 설정 불완전: {', '.join(missing)}")
            issues.append(f"이메일 설정 불완전: {', '.join(missing)}")
            recommendations.append(f"환경 변수 설정: {', '.join(missing)}")
    except Exception as e:
        print(f"  [ERROR] 이메일 설정 확인 실패: {str(e)}")
        issues.append("이메일 설정 확인 실패")
    
    print()
    print("=" * 80)
    print("종합 결과")
    print("=" * 80)
    
    passed = sum(1 for v in conditions.values() if v)
    total = len(conditions)
    
    print(f"\n통과 조건: {passed}/{total}")
    print()
    
    for condition, status in conditions.items():
        status_icon = "[OK]" if status else "[FAIL]"
        print(f"  {status_icon} {condition}")
    
    print()
    if passed == total:
        print("[결론] 자동 메일 발송이 가능합니다!")
        print()
        print("다음 DAG 실행 시 이메일이 자동으로 발송됩니다.")
        print(f"  - DAG 스케줄: 매 1분마다 실행")
        print(f"  - 다음 실행 예상: 약 1분 후")
    else:
        print("[결론] 현재 상태로는 자동 메일 발송이 불가능합니다.")
        print()
        if issues:
            print("발견된 문제점:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        if recommendations:
            print()
            print("권장 조치사항:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    try:
        check_all_conditions()
    except KeyboardInterrupt:
        print("\n\n중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

