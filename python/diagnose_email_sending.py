import sys
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config.settings import get_settings
    import pymysql
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("[WARNING] 데이터베이스 연결 모듈을 찾을 수 없습니다.")

def get_db_connection():
    if not DB_AVAILABLE:
        return None
    
    try:
        settings = get_settings()
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            port=settings.MYSQL_PORT,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        print(f"[ERROR] 데이터베이스 연결 실패: {str(e)}")
        return None

def check_notification_logs(limit: int = 50) -> List[Dict]:
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id,
                user_email,
                notification_type,
                status,
                sent_at,
                LEFT(message, 100) as message_preview,
                error_message
            FROM notification_logs
            ORDER BY sent_at DESC
            LIMIT %s
        """, (limit,))
        
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return logs
    except Exception as e:
        print(f"[ERROR] 로그 조회 실패: {str(e)}")
        if conn:
            conn.close()
        return []

def check_email_subscriptions() -> List[Dict]:
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id,
                name,
                email,
                is_email_consent,
                is_phone_consent,
                created_at,
                is_active
            FROM email_subscriptions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
        """)
        
        subscriptions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return subscriptions
    except Exception as e:
        print(f"[ERROR] 구독자 조회 실패: {str(e)}")
        if conn:
            conn.close()
        return []

def analyze_email_sending_status():
    print("=" * 80)
    print("이메일 발송 상태 분석")
    print("=" * 80)
    
    print("\n[1] 최근 발송 이력 (최근 20건)")
    print("-" * 80)
    logs = check_notification_logs(20)
    
    if not logs:
        print("  [WARNING] 발송 이력이 없습니다.")
        print("  가능한 원인:")
        print("    1. 이메일이 한 번도 발송되지 않았습니다")
        print("    2. 로그 저장이 실패하고 있습니다")
        print("    3. 데이터베이스 연결 문제")
    else:
        print(f"  총 {len(logs)}건의 발송 이력이 있습니다.\n")
        
        sent_count = len([l for l in logs if l.get('status') == 'sent'])
        failed_count = len([l for l in logs if l.get('status') == 'failed'])
        pending_count = len([l for l in logs if l.get('status') == 'pending'])
        
        print(f"  발송 상태:")
        print(f"    - 성공 (sent): {sent_count}건")
        print(f"    - 실패 (failed): {failed_count}건")
        print(f"    - 대기 (pending): {pending_count}건")
        
        print(f"\n  최근 5건 상세:")
        for i, log in enumerate(logs[:5], 1):
            sent_at = log.get('sent_at', 'N/A')
            if isinstance(sent_at, datetime):
                sent_at_str = sent_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                sent_at_str = str(sent_at)
            
            print(f"    {i}. {sent_at_str} | {log.get('user_email', 'N/A')} | {log.get('status', 'N/A')} | {log.get('notification_type', 'N/A')}")
            if log.get('error_message'):
                print(f"       오류: {log.get('error_message')[:100]}")
    
    print("\n[2] 오늘 발송된 이메일")
    print("-" * 80)
    today = datetime.now().date()
    today_logs = [l for l in logs if l.get('sent_at') and 
                  (isinstance(l.get('sent_at'), datetime) and l.get('sent_at').date() == today or
                   isinstance(l.get('sent_at'), str) and str(today) in str(l.get('sent_at')))]
    
    if not today_logs:
        print("  [WARNING] 오늘 발송된 이메일이 없습니다.")
    else:
        print(f"  오늘 발송된 이메일: {len(today_logs)}건")
        
        daily_reports = [l for l in today_logs 
                        if l.get('message_preview') and 
                        ('주식 분석 리포트' in str(l.get('message_preview')) or 
                         '일일 주식 분석' in str(l.get('message_preview')))]
        
        if daily_reports:
            print(f"  - 일일 분석 리포트: {len(daily_reports)}건")
            for log in daily_reports[:3]:
                print(f"    * {log.get('user_email')} - {log.get('status')} - {log.get('sent_at')}")
        else:
            print("  - 일일 분석 리포트: 0건 (오늘 발송되지 않음)")
    
    print("\n[3] 이메일 구독자 현황")
    print("-" * 80)
    subscriptions = check_email_subscriptions()
    
    if not subscriptions:
        print("  [WARNING] 구독자가 없습니다.")
        print("  이메일을 발송할 구독자가 없어서 발송이 되지 않을 수 있습니다.")
    else:
        email_consent_count = len([s for s in subscriptions if s.get('is_email_consent')])
        print(f"  전체 구독자: {len(subscriptions)}명")
        print(f"  이메일 동의 구독자: {email_consent_count}명")
        
        if email_consent_count == 0:
            print("  [WARNING] 이메일 동의한 구독자가 없습니다!")
            print("  이메일 발송을 위해서는 구독자가 이메일 동의를 해야 합니다.")
        else:
            print(f"\n  이메일 동의 구독자 목록:")
            for sub in subscriptions[:10]:
                if sub.get('is_email_consent'):
                    print(f"    - {sub.get('name', 'N/A')} ({sub.get('email', 'N/A')})")
    
    print("\n[4] 발송 스케줄 예측")
    print("-" * 80)
    print("  현재 DAG 설정:")
    print("    - 스케줄: */1 * * * * (매 1분마다 실행)")
    print("    - 일일 이메일 시간 체크: 주석 처리됨 (항상 발송 시도)")
    print("    - 중복 발송 방지: 주석 처리됨 (중복 발송 가능)")
    
    print("\n  예상 발송 동작:")
    print("    - 매 1분마다 DAG가 실행됩니다")
    print("    - 구독자가 있고 분석 데이터가 있으면 이메일을 발송합니다")
    print("    - 중복 방지 로직이 비활성화되어 있어 같은 이메일을 여러 번 발송할 수 있습니다")
    
    now = datetime.now()
    next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    print(f"\n  다음 DAG 실행 예상 시간: {next_minute.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n[5] 문제점 진단")
    print("-" * 80)
    
    issues = []
    recommendations = []
    
    if not logs:
        issues.append("발송 이력이 없습니다")
        recommendations.append("  - Airflow DAG 로그를 확인하세요")
        recommendations.append("  - Python API 서버가 실행 중인지 확인하세요")
        recommendations.append("  - 이메일 설정(EMAIL_SMTP_SERVER 등)이 올바른지 확인하세요")
    
    if not subscriptions:
        issues.append("구독자가 없습니다")
        recommendations.append("  - 구독자 등록 페이지에서 구독자를 추가하세요")
    
    if subscriptions:
        email_consent_count = len([s for s in subscriptions if s.get('is_email_consent')])
        if email_consent_count == 0:
            issues.append("이메일 동의한 구독자가 없습니다")
            recommendations.append("  - 구독자가 이메일 동의를 해야 합니다")
    
    if logs:
        failed_logs = [l for l in logs if l.get('status') == 'failed']
        if failed_logs:
            issues.append(f"최근 발송 실패가 {len(failed_logs)}건 있습니다")
            recommendations.append("  - 실패한 로그의 error_message를 확인하세요")
            recommendations.append("  - Python API 서버 상태를 확인하세요")
            recommendations.append("  - 이메일 SMTP 설정을 확인하세요")
    
    if not issues:
        print("  [OK] 특별한 문제점이 발견되지 않았습니다.")
    else:
        print("  발견된 문제점:")
        for i, issue in enumerate(issues, 1):
            print(f"    {i}. {issue}")
        
        if recommendations:
            print("\n  권장 조치사항:")
            for rec in recommendations:
                print(rec)
    
    print("\n[6] 백엔드 API 상태 확인")
    print("-" * 80)
    
    backend_host = os.getenv('BACKEND_HOST', 'localhost')
    try:
        response = requests.get(
            f'http://{backend_host}:8080/api/email-subscriptions/email-consent',
            timeout=5
        )
        if response.status_code == 200:
            print("  [OK] 백엔드 API 서버가 정상 작동 중입니다")
        else:
            print(f"  [WARNING] 백엔드 API 응답 코드: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] 백엔드 API 서버 연결 실패: {str(e)}")
        recommendations.append("  - Spring Boot 백엔드 서버를 실행하세요")
    
    print("\n[7] Python API 상태 확인")
    print("-" * 80)
    
    python_api_host = os.getenv('PYTHON_API_HOST', 'localhost')
    python_api_port = os.getenv('PYTHON_API_PORT', '8001')
    
    ports_to_try = [python_api_port, '9000', '8001']
    python_api_ok = False
    working_port = None
    
    for port in ports_to_try:
        try:
            response = requests.get(
                f'http://{python_api_host}:{port}/docs',
                timeout=5
            )
            if response.status_code == 200:
                print(f"  [OK] Python API 서버가 정상 작동 중입니다 ({python_api_host}:{port})")
                python_api_ok = True
                working_port = port
                break
        except:
            continue
    
    if not python_api_ok:
        print(f"  [ERROR] Python API 서버를 찾을 수 없습니다")
        recommendations.append("  - Python API 서버를 실행하세요: python start_python_api.py")
    
    print("\n[8] 분석 데이터 확인")
    print("-" * 80)
    
    analysis_data_available = False
    if python_api_ok and working_port:
        try:
            response = requests.get(
                f'http://{python_api_host}:{working_port}/api/analysis/all',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                valid_stocks = [s for s in data if s.get('currentPrice', 0) > 0]
                if valid_stocks:
                    print(f"  [OK] 분석 데이터가 있습니다: {len(valid_stocks)}개 종목")
                    analysis_data_available = True
                else:
                    print(f"  [WARNING] 분석 데이터는 있지만 유효한 가격 데이터가 없습니다: {len(data)}개 종목")
            else:
                print(f"  [WARNING] 분석 데이터 조회 실패: HTTP {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] 분석 데이터 조회 실패: {str(e)}")
    
    if not analysis_data_available:
        issues.append("분석 데이터가 없거나 유효하지 않습니다")
        recommendations.append("  - Python API가 주식 데이터를 수집하고 있는지 확인하세요")
    
    print("\n[9] 다음 발송 예측")
    print("-" * 80)
    
    can_send = True
    reasons = []
    
    if not subscriptions:
        can_send = False
        reasons.append("구독자가 없음")
    elif not email_consent_count:
        can_send = False
        reasons.append("이메일 동의한 구독자가 없음")
    
    if not analysis_data_available:
        can_send = False
        reasons.append("분석 데이터가 없음")
    
    if not python_api_ok:
        can_send = False
        reasons.append("Python API 서버가 실행되지 않음")
    
    if can_send:
        print("  [OK] 다음 DAG 실행 시 이메일 발송이 가능합니다!")
        print(f"  - 예상 발송 대상: {email_consent_count}명")
        print(f"  - 다음 DAG 실행 시간: {next_minute.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  - 예상 발송 시간: {next_minute.strftime('%H:%M:%S')} (약 1분 후)")
    else:
        print("  [WARNING] 다음 DAG 실행 시 이메일 발송이 불가능합니다.")
        print("  이유:")
        for reason in reasons:
            print(f"    - {reason}")
    
    print("\n" + "=" * 80)
    print("진단 완료")
    print("=" * 80)
    
    if recommendations:
        print("\n추가 권장 사항:")
        for rec in set(recommendations):
            print(rec)

def main():
    print("\n" + "=" * 80)
    print("Airflow 이메일 발송 진단 및 예측 도구")
    print("=" * 80 + "\n")
    
    if not DB_AVAILABLE:
        print("[ERROR] 데이터베이스 연결 모듈을 사용할 수 없습니다.")
        print("  필요한 패키지: pymysql, config.settings")
        sys.exit(1)
    
    try:
        analyze_email_sending_status()
    except KeyboardInterrupt:
        print("\n\n중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

