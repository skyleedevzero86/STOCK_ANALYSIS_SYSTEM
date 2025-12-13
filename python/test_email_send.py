

import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import get_settings

def test_email_config():
    print("=" * 60)
    print("1. 이메일 설정 확인")
    print("=" * 60)
    
    settings = get_settings()
    
    smtp_server = settings.EMAIL_SMTP_SERVER
    smtp_port = settings.EMAIL_SMTP_PORT
    user = settings.EMAIL_USER
    password = settings.EMAIL_PASSWORD
    
    print(f"SMTP 서버: {smtp_server}")
    print(f"SMTP 포트: {smtp_port}")
    print(f"이메일 사용자: {user}")
    print(f"비밀번호: {'*' * len(password) if password else '설정되지 않음'}")
    
    if not all([smtp_server, user, password]):
        missing = []
        if not smtp_server:
            missing.append("EMAIL_SMTP_SERVER")
        if not user:
            missing.append("EMAIL_USER")
        if not password:
            missing.append("EMAIL_PASSWORD")
        print(f"\n[ERROR] 설정이 완전하지 않습니다. 다음 환경 변수가 필요합니다: {', '.join(missing)}")
        return False
    
    print("\n[OK] 이메일 설정이 완료되었습니다.")
    return True

def test_smtp_connection():
    print("\n" + "=" * 60)
    print("2. SMTP 서버 연결 테스트")
    print("=" * 60)
    
    settings = get_settings()
    smtp_server = settings.EMAIL_SMTP_SERVER
    smtp_port = settings.EMAIL_SMTP_PORT
    
    try:
        print(f"연결 시도: {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        print("[OK] SMTP 서버 연결 성공")
        
        try:
            server.quit()
        except:
            pass
        
        return True
    except smtplib.SMTPConnectError as e:
        print(f"[ERROR] SMTP 서버 연결 실패: {str(e)}")
        print("   - 네트워크 연결을 확인하세요")
        print("   - 방화벽이 포트를 차단하고 있는지 확인하세요")
        return False
    except Exception as e:
        print(f"[ERROR] 연결 오류: {str(e)}")
        return False

def test_smtp_starttls():
    print("\n" + "=" * 60)
    print("3. STARTTLS 테스트")
    print("=" * 60)
    
    settings = get_settings()
    smtp_server = settings.EMAIL_SMTP_SERVER
    smtp_port = settings.EMAIL_SMTP_PORT
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        print("SMTP 서버 연결됨")
        
        print("STARTTLS 시작...")
        server.starttls()
        print("[OK] STARTTLS 성공")
        
        try:
            server.quit()
        except:
            pass
        
        return True
    except Exception as e:
        print(f"[ERROR] STARTTLS 실패: {str(e)}")
        print("   - SMTP 서버가 STARTTLS를 지원하는지 확인하세요")
        return False

def test_smtp_login():
    print("\n" + "=" * 60)
    print("4. SMTP 로그인 테스트")
    print("=" * 60)
    
    settings = get_settings()
    smtp_server = settings.EMAIL_SMTP_SERVER
    smtp_port = settings.EMAIL_SMTP_PORT
    user = settings.EMAIL_USER
    password = settings.EMAIL_PASSWORD
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        
        print(f"로그인 시도: {user}")
        server.login(user, password)
        print("[OK] SMTP 로그인 성공")
        
        try:
            server.quit()
        except:
            pass
        
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] 인증 실패: {str(e)}")
        print("\n가능한 원인:")
        print("   1. 이메일 주소 또는 비밀번호가 잘못되었습니다")
        print("   2. 네이버 메일의 경우 '앱 비밀번호'를 사용해야 합니다")
        print("   3. 2단계 인증이 활성화되어 있는 경우 앱 비밀번호가 필요합니다")
        print("\n네이버 메일 앱 비밀번호 설정 방법:")
        print("   1. 네이버 메일 로그인")
        print("   2. 설정 > 보안 > 2단계 인증 > 앱 비밀번호")
        print("   3. 앱 비밀번호 생성 후 사용")
        return False
    except Exception as e:
        print(f"[ERROR] 로그인 오류: {str(e)}")
        return False

def test_email_send():
    print("\n" + "=" * 60)
    print("5. 이메일 발송 테스트")
    print("=" * 60)
    
    settings = get_settings()
    smtp_server = settings.EMAIL_SMTP_SERVER
    smtp_port = settings.EMAIL_SMTP_PORT
    user = settings.EMAIL_USER
    password = settings.EMAIL_PASSWORD
    
    test_email = input("테스트 이메일 주소를 입력하세요 (Enter로 건너뛰기): ").strip()
    if not test_email:
        print("이메일 발송 테스트를 건너뜁니다.")
        return None
    
    try:
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = test_email
        msg['Subject'] = "이메일 발송 테스트"
        
        body = "이것은 이메일 발송 테스트 메시지입니다.\n\n발송 시간: " + str(os.popen('date /t').read().strip())
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.starttls()
        server.login(user, password)
        
        print(f"이메일 발송 시도: {test_email}")
        failed_recipients = server.send_message(msg)
        
        if failed_recipients:
            print(f"[ERROR] 이메일 발송 실패: {failed_recipients}")
            return False
        else:
            print("[OK] 이메일 발송 성공!")
            print(f"   수신자: {test_email}")
            return True
        
        server.quit()
    except Exception as e:
        print(f"[ERROR] 이메일 발송 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("이메일 발송 진단 도구")
    print("=" * 60 + "\n")
    
    if not test_email_config():
        print("\n[ERROR] 이메일 설정이 완전하지 않습니다. 설정을 확인하세요.")
        sys.exit(1)
    
    if not test_smtp_connection():
        print("\n[ERROR] SMTP 서버에 연결할 수 없습니다.")
        sys.exit(1)
    
    if not test_smtp_starttls():
        print("\n[ERROR] STARTTLS가 실패했습니다.")
        sys.exit(1)
    
    if not test_smtp_login():
        print("\n[ERROR] SMTP 로그인이 실패했습니다.")
        print("\n[TIP] 네이버 메일 사용 시:")
        print("   - 일반 비밀번호가 아닌 '앱 비밀번호'를 사용해야 합니다")
        print("   - 네이버 > 메일 > 설정 > 보안 > 2단계 인증 > 앱 비밀번호")
        sys.exit(1)
    
    result = test_email_send()
    
    print("\n" + "=" * 60)
    if result is True:
        print("[OK] 모든 테스트 통과! 이메일 발송이 정상적으로 작동합니다.")
    elif result is False:
        print("[ERROR] 이메일 발송에 실패했습니다.")
    else:
        print("[WARNING] 이메일 발송 테스트를 건너뛰었습니다.")
    print("=" * 60 + "\n")

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

