from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
import requests
import json
import logging
import os

default_args = {
    'owner': 'stock-analysis',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


dag = DAG(
    'email_notification_dag',
    default_args=default_args,
    description='주식 분석 이메일 알림 발송',
    #schedule=''0 9 * * 1-5', # 평일 오전 9시
    schedule='*/1 * * * *',
    catchup=False,
    tags=['stock', 'email', 'notification']
)

def get_subscribers():
    try:
        backend_host = os.getenv('BACKEND_HOST', 'localhost')
        response = requests.get(f'http://{backend_host}:8080/api/email-subscriptions/email-consent', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data']['subscriptions']
        return []
    except Exception as e:
        logging.error(f"구독자 목록 조회 실패: {str(e)}")
        return []

def get_sms_subscribers():
    try:
        backend_host = os.getenv('BACKEND_HOST', 'localhost')
        response = requests.get(f'http://{backend_host}:8080/api/email-subscriptions/phone-consent', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data']['subscriptions']
        return []
    except Exception as e:
        logging.error(f"SMS 구독자 목록 조회 실패: {str(e)}")
        return []

def get_stock_analysis():
    try:
        python_api_host = os.getenv('PYTHON_API_HOST', 'localhost')
        response = requests.get(f'http://{python_api_host}:9000/api/analysis/all', timeout=30)
        if response.status_code == 200:
            data = response.json()
            logging.info(f"분석 데이터 조회 성공: {len(data)}개 종목")
            
            for stock in data:
                symbol = stock.get('symbol', 'N/A')
                price = stock.get('currentPrice', 0)
                trend = stock.get('trend', 'N/A')
                signal = stock.get('signals', {}).get('signal', 'N/A') if isinstance(stock.get('signals'), dict) else 'N/A'
                logging.info(f"  {symbol}: 가격=${price:.2f}, 트렌드={trend}, 신호={signal}")
            
            return data
        else:
            logging.error(f"주식 분석 데이터 조회 실패: HTTP {response.status_code}")
            logging.error(f"응답 내용: {response.text[:200]}")
        return []
    except Exception as e:
        logging.error(f"주식 분석 데이터 조회 실패: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return []

def send_email_notification(to_email, subject, body, source="airflow"):
    try:
        python_api_host = os.getenv('PYTHON_API_HOST', 'localhost')
        backend_host = os.getenv('BACKEND_HOST', 'localhost')
        
        response = requests.post(f'http://{python_api_host}:9000/api/notifications/email', 
                               params={
                                   'to_email': to_email,
                                   'subject': subject,
                                   'body': body
                               },
                               timeout=10)
        
        if response.status_code == 200:
            try:
                requests.post(
                    f'http://{backend_host}:8080/api/admin/save-notification-log',
                    json={
                        'userEmail': to_email,
                        'subject': subject,
                        'message': body,
                        'status': 'sent',
                        'source': source,
                        'notificationType': 'email'
                    },
                    timeout=5
                )
            except Exception as e:
                logging.warning(f"이메일 발송 로그 저장 실패: {str(e)}")
        
        return response.status_code == 200
    except Exception as e:
        logging.error(f"이메일 발송 실패 ({to_email}): {str(e)}")
        return False

def send_sms_notification(to_phone, message, source="airflow", user_email=None):
    try:
        python_api_host = os.getenv('PYTHON_API_HOST', 'localhost')
        backend_host = os.getenv('BACKEND_HOST', 'localhost')
        
        response = requests.post(f'http://{python_api_host}:9000/api/notifications/sms', 
                               params={
                                   'to_phone': to_phone,
                                   'message': message
                               },
                               timeout=10)
        
        if response.status_code == 200:
            try:
                requests.post(
                    f'http://{backend_host}:8080/api/admin/save-notification-log',
                    json={
                        'userEmail': user_email if user_email else to_phone,
                        'subject': None,
                        'message': message,
                        'status': 'sent',
                        'source': source,
                        'notificationType': 'sms'
                    },
                    timeout=5
                )
            except Exception as e:
                logging.warning(f"SMS 발송 로그 저장 실패: {str(e)}")
        
        return response.status_code == 200
    except Exception as e:
        logging.error(f"SMS 발송 실패 ({to_phone}): {str(e)}")
        return False

def generate_email_content(analysis_data):
    if not analysis_data:
        return "분석 데이터가 없습니다."
    
    valid_stocks = [s for s in analysis_data if s.get('currentPrice', 0) > 0]
    
    if not valid_stocks:
        return "유효한 주식 데이터가 없습니다. Python API 서버가 정상적으로 실행 중인지 확인하세요."
    
    trend_map = {
        'bullish': '상승',
        'bearish': '하락',
        'neutral': '중립'
    }
    
    signal_map = {
        'buy': '매수',
        'sell': '매도',
        'hold': '보유'
    }
    
    content = f"""
주식 분석 리포트 - {datetime.now().strftime('%Y년 %m월 %d일')}

=== 주요 종목 분석 결과 ===

"""
    
    for stock in valid_stocks[:5]:  
        symbol = stock.get('symbol', 'N/A')
        price = stock.get('currentPrice', 0)
        change_percent = stock.get('changePercent', 0)
        trend = stock.get('trend', 'neutral')
        signals = stock.get('signals', {})
        
        if isinstance(signals, dict):
            signal = signals.get('signal', 'hold')
        else:
            signal = 'hold'
        
        trend_ko = trend_map.get(trend.lower(), trend)
        signal_ko = signal_map.get(signal.lower(), signal)
        
        if price > 0:
            content += f"""
{symbol}
   현재가: ${price:.2f} ({change_percent:+.2f}%)
   트렌드: {trend_ko} ({trend})
   신호: {signal_ko} ({signal})
"""
        else:
            content += f"""
{symbol}
   현재가: 데이터 없음
   트렌드: {trend_ko} ({trend})
   신호: {signal_ko} ({signal})
"""
    
    content += f"""

=== 전체 분석 요약 ===
• 분석 종목 수: {len(valid_stocks)}/{len(analysis_data)}
• 상승 종목: {len([s for s in valid_stocks if s.get('changePercent', 0) > 0])}
• 하락 종목: {len([s for s in valid_stocks if s.get('changePercent', 0) < 0])}

더 자세한 분석은 대시보드에서 확인하세요: http://localhost:8080

---
주식 분석 시스템
"""
    
    return content

def generate_sms_content(analysis_data):
    if not analysis_data:
        return "분석 데이터가 없습니다."
    
    date_str = datetime.now().strftime('%m/%d')
    top_stocks = analysis_data[:3]
    
    content = f"[주식분석 {date_str}]\n"
    
    for stock in top_stocks:
        symbol = stock.get('symbol', 'N/A')
        price = stock.get('currentPrice', 0)
        change_percent = stock.get('changePercent', 0)
        signal = stock.get('signals', {}).get('signal', 'hold')
        
        content += f"{symbol} ${price:.1f} ({change_percent:+.1f}%) {signal}\n"
    
    content += f"상승:{len([s for s in analysis_data if s.get('changePercent', 0) > 0])} 하락:{len([s for s in analysis_data if s.get('changePercent', 0) < 0])}"
    
    return content

def check_daily_email_sent_today(email):
    try:
        backend_host = os.getenv('BACKEND_HOST', 'localhost')
        response = requests.get(
            f'http://{backend_host}:8080/api/admin/check-daily-email',
            params={'email': email},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('sent', False)
        return False
    except Exception as e:
        logging.warning(f"일일 분석 메일 발송 여부 확인 실패 ({email}): {str(e)}")
        return False

def check_daily_sms_sent_today(phone):
    try:
        backend_host = os.getenv('BACKEND_HOST', 'localhost')
        response = requests.get(
            f'http://{backend_host}:8080/api/admin/check-daily-sms',
            params={'phone': phone},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('sent', False)
        return False
    except Exception as e:
        logging.warning(f"일일 분석 SMS 발송 여부 확인 실패 ({phone}): {str(e)}")
        return False

def send_daily_analysis_emails():
    logging.info("일일 분석 이메일 발송 시작")
    
    subscribers = get_subscribers()
    if not subscribers:
        logging.info("구독자가 없습니다.")
        return
    
    analysis_data = get_stock_analysis()
    
    if not analysis_data:
        logging.warning("분석 데이터가 없습니다. 일일 분석 메일을 발송하지 않습니다.")
        return
    
    email_content = generate_email_content(analysis_data)
    subject = f"주식 분석 리포트 - {datetime.now().strftime('%Y년 %m월 %d일')}"
    
    success_count = 0
    for subscriber in subscribers:
        is_email_consent = subscriber.get('isEmailConsent', False)
        if not is_email_consent:
            logging.info(f"이메일 동의하지 않은 구독자: {subscriber.get('email')}")
            continue
        
        email = subscriber.get('email')
        if not email:
            continue
        
        if check_daily_email_sent_today(email):
            logging.info(f"오늘 이미 일일 분석 메일을 받은 구독자: {email}")
            continue
        
        name = subscriber.get('name', '고객')
        personalized_content = f"안녕하세요, {name}님!\n\n{email_content}"
        
        if send_email_notification(email, subject, personalized_content):
            success_count += 1
            logging.info(f"이메일 발송 성공: {email}")
        else:
            logging.error(f"이메일 발송 실패: {email}")
    
    logging.info(f"이메일 발송 완료: {success_count}/{len(subscribers)}")

def send_daily_analysis_sms():
    logging.info("일일 분석 SMS 발송 시작")
    
    subscribers = get_sms_subscribers()
    if not subscribers:
        logging.info("SMS 구독자가 없습니다.")
        return
    
    analysis_data = get_stock_analysis()
    
    if not analysis_data:
        logging.warning("분석 데이터가 없습니다. 일일 분석 SMS를 발송하지 않습니다.")
        return
    
    sms_content = generate_sms_content(analysis_data)
    
    success_count = 0
    for subscriber in subscribers:
        is_phone_consent = subscriber.get('isPhoneConsent', False)
        if not is_phone_consent:
            logging.info(f"SMS 동의하지 않은 구독자: {subscriber.get('phone')}")
            continue
        
        phone = subscriber.get('phone')
        if not phone:
            continue
        
        phone = phone.replace("-", "").replace(" ", "").replace("+82", "0")
        
        if check_daily_sms_sent_today(phone):
            logging.info(f"오늘 이미 일일 분석 SMS를 받은 구독자: {phone}")
            continue
        
        name = subscriber.get('name', '고객')
        email = subscriber.get('email', '')
        personalized_content = f"{name}님, {sms_content}"
        
        if send_sms_notification(phone, personalized_content, source="airflow", user_email=email):
            success_count += 1
            logging.info(f"SMS 발송 성공: {phone}")
        else:
            logging.error(f"SMS 발송 실패: {phone}")
    
    logging.info(f"SMS 발송 완료: {success_count}/{len(subscribers)}")

def check_welcome_email_sent(email):
    try:
        backend_host = os.getenv('BACKEND_HOST', 'localhost')
        response = requests.get(
            f'http://{backend_host}:8080/api/admin/check-welcome-email',
            params={'email': email},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('sent', False)
        return False
    except Exception as e:
        logging.warning(f"환영 메일 발송 여부 확인 실패 ({email}): {str(e)}")
        return False

def check_welcome_sms_sent(phone):
    try:
        backend_host = os.getenv('BACKEND_HOST', 'localhost')
        response = requests.get(
            f'http://{backend_host}:8080/api/admin/check-welcome-sms',
            params={'phone': phone},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('sent', False)
        return False
    except Exception as e:
        logging.warning(f"환영 SMS 발송 여부 확인 실패 ({phone}): {str(e)}")
        return False

def send_welcome_emails(**context):
    logging.info("환영 메일 발송 시작")
    
    subscribers = get_subscribers()
    if not subscribers:
        logging.info("구독자가 없습니다.")
        return
    
    current_time = datetime.now()
    welcome_wait_minutes = 5
    
    recent_subscribers = []
    sent_emails = set()
    
    for subscriber in subscribers:
        is_email_consent = subscriber.get('isEmailConsent', False)
        if not is_email_consent:
            logging.info(f"이메일 동의하지 않은 구독자: {subscriber.get('email')}")
            continue
        
        created_at_str = subscriber.get('createdAt')
        if not created_at_str:
            continue
        
        try:
            created_at_str = created_at_str.replace('Z', '+00:00')
            
            if '.' in created_at_str:
                created_at_str = created_at_str.split('.')[0]
            
            if 'T' in created_at_str:
                if '+' in created_at_str or created_at_str.endswith('Z'):
                    created_at = datetime.fromisoformat(created_at_str)
                else:
                    created_at = datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%S')
            else:
                created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            
            if created_at.tzinfo:
                created_at = created_at.replace(tzinfo=None)
            
            time_diff = current_time - created_at
            wait_time = timedelta(minutes=welcome_wait_minutes)
            
            if wait_time <= time_diff <= timedelta(hours=24):
                email = subscriber.get('email')
                if email and email not in sent_emails:
                    if check_welcome_email_sent(email):
                        logging.info(f"이미 환영 메일을 받은 구독자: {email}")
                        continue
                    
                    recent_subscribers.append(subscriber)
                    sent_emails.add(email)
                    logging.info(f"최근 가입 구독자 발견: {email} (가입 후 {time_diff.total_seconds()/60:.1f}분 경과)")
        except Exception as e:
            logging.warning(f"구독자 가입 시간 파싱 실패: {subscriber.get('email')} - {str(e)}")
            logging.debug(f"createdAt 값: {created_at_str}")
    
    if not recent_subscribers:
        logging.info(f"최근 {welcome_wait_minutes}분 이상 지난 구독자가 없거나 이미 환영 메일을 받은 구독자입니다.")
        return
    
    welcome_content = f"""
주식 분석 시스템에 오신 것을 환영합니다!

안녕하세요, 구독자님!

주식 분석 시스템에 가입해 주셔서 감사합니다.
이제 주식 시장의 최신 분석 리포트와 알림을 이메일로 받아보실 수 있습니다.

=== 서비스 안내 ===
• 일일 주식 분석 리포트: 매일 오전 9시에 주요 종목 분석 결과를 발송합니다
• 이상 패턴 알림: 급격한 가격 변동이나 이상 패턴이 감지되면 즉시 알림을 발송합니다
• 맞춤형 분석: 다양한 기술적 지표를 활용한 종목별 분석을 제공합니다

더 자세한 분석은 대시보드에서 확인하세요: http://localhost:8080

앞으로도 유용한 정보를 제공하도록 노력하겠습니다.
감사합니다.

---
주식 분석 시스템
{current_time.strftime('%Y년 %m월 %d일')}
"""
    
    subject = "주식 분석 시스템 환영 메일"
    
    success_count = 0
    for subscriber in recent_subscribers:
        email = subscriber.get('email')
        name = subscriber.get('name', '고객')
        
        if email:
            personalized_content = f"안녕하세요, {name}님!\n\n{welcome_content}"
            
            if send_email_notification(email, subject, personalized_content):
                success_count += 1
                logging.info(f"환영 메일 발송 성공: {email}")
            else:
                logging.error(f"환영 메일 발송 실패: {email}")
    
    logging.info(f"환영 메일 발송 완료: {success_count}/{len(recent_subscribers)}")

def send_welcome_sms(**context):
    logging.info("환영 SMS 발송 시작")
    
    subscribers = get_sms_subscribers()
    if not subscribers:
        logging.info("SMS 구독자가 없습니다.")
        return
    
    current_time = datetime.now()
    welcome_wait_minutes = 5
    
    recent_subscribers = []
    sent_phones = set()
    
    for subscriber in subscribers:
        is_phone_consent = subscriber.get('isPhoneConsent', False)
        if not is_phone_consent:
            logging.info(f"SMS 동의하지 않은 구독자: {subscriber.get('phone')}")
            continue
        
        created_at_str = subscriber.get('createdAt')
        if not created_at_str:
            continue
        
        try:
            created_at_str = created_at_str.replace('Z', '+00:00')
            
            if '.' in created_at_str:
                created_at_str = created_at_str.split('.')[0]
            
            if 'T' in created_at_str:
                if '+' in created_at_str or created_at_str.endswith('Z'):
                    created_at = datetime.fromisoformat(created_at_str)
                else:
                    created_at = datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%S')
            else:
                created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            
            if created_at.tzinfo:
                created_at = created_at.replace(tzinfo=None)
            
            time_diff = current_time - created_at
            wait_time = timedelta(minutes=welcome_wait_minutes)
            
            if wait_time <= time_diff <= timedelta(hours=24):
                phone = subscriber.get('phone')
                if phone and phone not in sent_phones:
                    phone = phone.replace("-", "").replace(" ", "").replace("+82", "0")
                    
                    if check_welcome_sms_sent(phone):
                        logging.info(f"이미 환영 SMS를 받은 구독자: {phone}")
                        continue
                    
                    recent_subscribers.append(subscriber)
                    sent_phones.add(phone)
                    logging.info(f"최근 가입 SMS 구독자 발견: {phone} (가입 후 {time_diff.total_seconds()/60:.1f}분 경과)")
        except Exception as e:
            logging.warning(f"구독자 가입 시간 파싱 실패: {subscriber.get('phone')} - {str(e)}")
            logging.debug(f"createdAt 값: {created_at_str}")
    
    if not recent_subscribers:
        logging.info(f"최근 {welcome_wait_minutes}분 이상 지난 SMS 구독자가 없거나 이미 환영 SMS를 받은 구독자입니다.")
        return
    
    welcome_content = f"""주식 분석 시스템에 오신 것을 환영합니다!

가입해 주셔서 감사합니다.
이제 주식 시장의 최신 분석 리포트와 알림을 문자로 받아보실 수 있습니다.

서비스 안내:
• 일일 주식 분석 리포트: 매일 오전 9시
• 이상 패턴 알림: 급격한 가격 변동 시 즉시 알림
• 맞춤형 분석 제공

더 자세한 분석은 대시보드에서 확인하세요:
http://localhost:8080

주식 분석 시스템"""
    
    success_count = 0
    for subscriber in recent_subscribers:
        phone = subscriber.get('phone')
        name = subscriber.get('name', '고객')
        
        if phone:
            phone = phone.replace("-", "").replace(" ", "").replace("+82", "0")
            email = subscriber.get('email', '')
            personalized_content = f"{name}님, {welcome_content}"
            
            if send_sms_notification(phone, personalized_content, source="airflow", user_email=email):
                success_count += 1
                logging.info(f"환영 SMS 발송 성공: {phone}")
            else:
                logging.error(f"환영 SMS 발송 실패: {phone}")
    
    logging.info(f"환영 SMS 발송 완료: {success_count}/{len(recent_subscribers)}")

def send_alert_emails():
    logging.info("알림 이메일 발송 시작")
    
    subscribers = get_subscribers()
    if not subscribers:
        return
    
    analysis_data = get_stock_analysis()
    if not analysis_data:
        return
    
    alert_stocks = []
    for stock in analysis_data:
        anomalies = stock.get('anomalies', [])
        if anomalies:
            alert_stocks.append(stock)
    
    if not alert_stocks:
        logging.info("알림할 이상 패턴이 없습니다.")
        return
    
    alert_content = f"""
주식 이상 패턴 알림 - {datetime.now().strftime('%Y년 %m월 %d일 %H시')}

=== 이상 패턴 감지 종목 ===

"""
    
    for stock in alert_stocks:
        symbol = stock.get('symbol', 'N/A')
        price = stock.get('currentPrice', 0)
        anomalies = stock.get('anomalies', [])
        
        alert_content += f"""
{symbol} (${price:.2f})
"""
        for anomaly in anomalies:
            alert_content += f"   {anomaly.get('message', '이상 패턴 감지')}\n"
    
    alert_content += f"""

자세한 분석은 대시보드에서 확인하세요: http://localhost:8080

---
주식 분석 시스템
"""
    
    subject = f"주식 이상 패턴 알림 - {datetime.now().strftime('%m월 %d일')}"
    
    for subscriber in subscribers:
        email = subscriber.get('email')
        name = subscriber.get('name', '고객')
        
        if email:
            personalized_content = f"안녕하세요, {name}님!\n\n{alert_content}"
            send_email_notification(email, subject, personalized_content)

def send_alert_sms():
    logging.info("알림 SMS 발송 시작")
    
    subscribers = get_sms_subscribers()
    if not subscribers:
        return
    
    analysis_data = get_stock_analysis()
    if not analysis_data:
        return
    
    alert_stocks = []
    for stock in analysis_data:
        anomalies = stock.get('anomalies', [])
        if anomalies:
            alert_stocks.append(stock)
    
    if not alert_stocks:
        logging.info("알림할 이상 패턴이 없습니다.")
        return
    
    date_str = datetime.now().strftime('%m/%d %H시')
    alert_content = f"[이상패턴 알림 {date_str}]\n"
    
    for stock in alert_stocks[:3]:
        symbol = stock.get('symbol', 'N/A')
        price = stock.get('currentPrice', 0)
        anomalies = stock.get('anomalies', [])
        
        alert_content += f"{symbol} ${price:.1f}\n"
        for anomaly in anomalies[:1]:
            alert_content += f"{anomaly.get('message', '이상 패턴')}\n"
    
    alert_content += "자세한 분석은 대시보드에서 확인하세요."
    
    for subscriber in subscribers:
        phone = subscriber.get('phone')
        name = subscriber.get('name', '고객')
        email = subscriber.get('email', '')
        
        if phone:
            phone = phone.replace("-", "").replace(" ", "").replace("+82", "0")
            personalized_content = f"{name}님, {alert_content}"
            send_sms_notification(phone, personalized_content, source="airflow", user_email=email)

get_subscribers_task = PythonOperator(
    task_id='get_subscribers',
    python_callable=get_subscribers,
    dag=dag
)

get_analysis_task = PythonOperator(
    task_id='get_stock_analysis',
    python_callable=get_stock_analysis,
    dag=dag
)

send_daily_emails_task = PythonOperator(
    task_id='send_daily_analysis_emails',
    python_callable=send_daily_analysis_emails,
    dag=dag
)

send_alert_emails_task = PythonOperator(
    task_id='send_alert_emails',
    python_callable=send_alert_emails,
    dag=dag
)

send_welcome_emails_task = PythonOperator(
    task_id='send_welcome_emails',
    python_callable=send_welcome_emails,
    dag=dag
)

send_daily_sms_task = PythonOperator(
    task_id='send_daily_analysis_sms',
    python_callable=send_daily_analysis_sms,
    dag=dag
)

send_alert_sms_task = PythonOperator(
    task_id='send_alert_sms',
    python_callable=send_alert_sms,
    dag=dag
)

send_welcome_sms_task = PythonOperator(
    task_id='send_welcome_sms',
    python_callable=send_welcome_sms,
    dag=dag
)

get_subscribers_task >> send_welcome_emails_task
get_subscribers_task >> send_daily_emails_task
get_analysis_task >> send_daily_emails_task
get_analysis_task >> send_alert_emails_task

get_subscribers_task >> send_welcome_sms_task
get_subscribers_task >> send_daily_sms_task
get_analysis_task >> send_daily_sms_task
get_analysis_task >> send_alert_sms_task
