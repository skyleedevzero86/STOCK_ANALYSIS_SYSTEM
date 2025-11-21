import sys
from utils.service_checker import ServiceChecker
from utils.print_utils import PrintFormatter
from utils.db_checker import DatabaseChecker

def check_all_services():
    PrintFormatter.print_header("서비스 상태 확인")
    
    hosts = ['localhost', 'host.docker.internal']
    all_results = {}
    
    for host in hosts:
        print(f"\n[{host}] 테스트:")
        PrintFormatter.print_status("호스트", True, host)
        
        results = ServiceChecker.check_all_services(host)
        all_results[host] = results
        
        for service_key, (is_online, response) in results.items():
            config = ServiceChecker.SERVICES[service_key]
            if is_online:
                PrintFormatter.print_status(config.name, True, f"{host}:{config.port}")
            else:
                error_msg = response.error if response.error else f"HTTP {response.status_code}" if response.status_code else "연결 실패"
                PrintFormatter.print_error(config.name, error_msg)
    
    return all_results

def check_subscribers():
    PrintFormatter.print_header("이메일 구독자 확인")
    
    count, subscriptions = ServiceChecker.check_spring_boot_subscribers()
    
    if count > 0:
        print(f"\n총 {count}명의 이메일 동의 구독자가 있습니다.\n")
        for sub in subscriptions[:10]:
            print(f"이름: {sub.get('name', 'N/A')}")
            print(f"이메일: {sub.get('email', 'N/A')}")
            print(f"가입일: {sub.get('createdAt', 'N/A')}")
            print(PrintFormatter.divider())
    else:
        print("\n이메일 동의 구독자가 없습니다.")
    
    return count

def check_notification_logs(hours: int = 24):
    PrintFormatter.print_header(f"알림 발송 로그 확인 (최근 {hours}시간)")
    
    sent, failed, pending, logs = DatabaseChecker.check_notification_logs(hours)
    
    if not logs:
        print(f"\n최근 {hours}시간 동안 발송된 알림이 없습니다.")
        return
    
    print(f"\n총 {len(logs)}건의 발송 로그가 있습니다.\n")
    
    for log in logs[:10]:
        status = log.get('status', 'unknown')
        icon = PrintFormatter.status_icon(status == 'sent')
        print(f"{icon} [{status.upper()}] {log.get('sent_at', 'N/A')}")
        print(f"   수신자: {log.get('user_email', 'N/A')}")
        print(f"   종목: {log.get('symbol') or '전체'}")
        print(f"   유형: {log.get('notification_type', 'N/A')}")
        if log.get('error_message'):
            print(f"   오류: {log.get('error_message')}")
        print()
    
    print(PrintFormatter.divider())
    print(f"발송 성공: {sent}건")
    print(f"발송 실패: {failed}건")
    print(f"대기 중: {pending}건")

def check_airflow_dag():
    PrintFormatter.print_header("Airflow DAG 확인")
    
    exists, dag_info = ServiceChecker.check_airflow_dag()
    
    if exists and dag_info:
        print("email_notification_dag가 등록되어 있습니다.")
        
        runs = dag_info.get('runs', [])
        if runs:
            print(f"\n최근 실행 내역:")
            for run in runs[:5]:
                state = run.get('state', 'unknown')
                icon = PrintFormatter.status_icon(state == 'success')
                print(f"{icon} 상태: {state}")
                print(f"   시작: {run.get('start_date', 'N/A')}")
                print(f"   종료: {run.get('end_date', 'N/A')}")
                print()
        else:
            print("아직 실행된 DAG가 없습니다.")
    else:
        PrintFormatter.print_error("Airflow DAG", "DAG를 찾을 수 없습니다.")

def check_email_config():
    PrintFormatter.print_header("이메일 설정 확인")
    
    is_valid, config = ServiceChecker.check_email_config()
    
    print(f"SMTP 서버: {config['smtp_server']}")
    print(f"SMTP 포트: {config['smtp_port']}")
    print(f"이메일 사용자: {config['user']}")
    print(f"이메일 비밀번호: {config['password']}")
    
    if is_valid:
        PrintFormatter.print_status("이메일 설정", True)
    else:
        PrintFormatter.print_error("이메일 설정", "설정이 완전하지 않습니다.")

def check_database_subscriptions():
    PrintFormatter.print_header("데이터베이스 구독자 확인")
    
    count, subscribers = DatabaseChecker.check_subscriptions()
    
    if subscribers:
        print(f"\n총 {len(subscribers)}명의 구독자가 있습니다.\n")
        
        email_consent_count = 0
        for sub in subscribers:
            is_email_consent = sub.get('is_email_consent', False)
            is_active = sub.get('is_active', False)
            
            consent_status = "동의" if is_email_consent else "거부"
            active_status = "활성" if is_active else "비활성"
            
            print(f"ID: {sub.get('id')}")
            print(f"  이름: {sub.get('name', 'N/A')}")
            print(f"  이메일: {sub.get('email', 'N/A')}")
            print(f"  이메일 동의: {consent_status}")
            print(f"  전화 동의: {'동의' if sub.get('is_phone_consent') else '거부'}")
            print(f"  상태: {active_status}")
            print(f"  가입일: {sub.get('created_at', 'N/A')}")
            print()
            
            if is_email_consent and is_active:
                email_consent_count += 1
        
        print(PrintFormatter.divider())
        print(f"이메일 발송 가능한 구독자: {email_consent_count}명")
    else:
        print("\n등록된 구독자가 없습니다.")
    
    return count

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='서비스 상태 확인 도구')
    parser.add_argument('--all', action='store_true', help='모든 확인 수행')
    parser.add_argument('--services', action='store_true', help='서비스 상태 확인')
    parser.add_argument('--subscribers', action='store_true', help='구독자 확인')
    parser.add_argument('--logs', action='store_true', help='발송 로그 확인')
    parser.add_argument('--airflow', action='store_true', help='Airflow DAG 확인')
    parser.add_argument('--email-config', action='store_true', help='이메일 설정 확인')
    parser.add_argument('--db-subscribers', action='store_true', help='DB 구독자 확인')
    parser.add_argument('--hours', type=int, default=24, help='로그 확인 시간 범위 (기본: 24)')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        args.all = True
    
    try:
        if args.all or args.services:
            check_all_services()
        
        if args.all or args.subscribers:
            check_subscribers()
        
        if args.all or args.db_subscribers:
            check_database_subscriptions()
        
        if args.all or args.logs:
            check_notification_logs(args.hours)
        
        if args.all or args.airflow:
            check_airflow_dag()
        
        if args.all or args.email_config:
            check_email_config()
        
        print(PrintFormatter.header("확인 완료"))
        
    except KeyboardInterrupt:
        print("\n\n중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


