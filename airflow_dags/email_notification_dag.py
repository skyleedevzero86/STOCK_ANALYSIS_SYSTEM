from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import requests
import json
import logging

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
    schedule_interval='0 9 * * 1-5',  # 평일 오전 9시
    catchup=False,
    tags=['stock', 'email', 'notification']
)

def get_subscribers():
    try:
        response = requests.get('http://localhost:8080/api/email-subscriptions/email-consent')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data']['subscriptions']
        return []
    except Exception as e:
        logging.error(f"구독자 목록 조회 실패: {str(e)}")
        return []

def get_stock_analysis():
    try:
        response = requests.get('http://localhost:8000/api/analysis/all')
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        logging.error(f"주식 분석 데이터 조회 실패: {str(e)}")
        return []

def send_email_notification(to_email, subject, body):
    try:
        response = requests.post('http://localhost:8000/api/notifications/email', 
                               params={
                                   'to_email': to_email,
                                   'subject': subject,
                                   'body': body
                               })
        return response.status_code == 200
    except Exception as e:
        logging.error(f"이메일 발송 실패 ({to_email}): {str(e)}")
        return False

def generate_email_content(analysis_data):
    if not analysis_data:
        return "분석 데이터가 없습니다."
    
    content = f"""
주식 분석 리포트 - {datetime.now().strftime('%Y년 %m월 %d일')}

=== 주요 종목 분석 결과 ===

"""
    
    for stock in analysis_data[:5]:  
        symbol = stock.get('symbol', 'N/A')
        price = stock.get('current_price', 0)
        change_percent = stock.get('change_percent', 0)
        trend = stock.get('trend', 'neutral')
        signal = stock.get('signals', {}).get('signal', 'hold')
        
        content += f"""
{symbol}
   현재가: ${price:.2f} ({change_percent:+.2f}%)
   트렌드: {trend}
   신호: {signal}
"""
    
    content += f"""

=== 전체 분석 요약 ===
• 분석 종목 수: {len(analysis_data)}
• 상승 종목: {len([s for s in analysis_data if s.get('change_percent', 0) > 0])}
• 하락 종목: {len([s for s in analysis_data if s.get('change_percent', 0) < 0])}

더 자세한 분석은 대시보드에서 확인하세요: http://localhost:8080

---
주식 분석 시스템
"""
    
    return content

def send_daily_analysis_emails():
    logging.info("일일 분석 이메일 발송 시작")
    
    subscribers = get_subscribers()
    if not subscribers:
        logging.info("구독자가 없습니다.")
        return
    
    analysis_data = get_stock_analysis()
    if not analysis_data:
        logging.warning("분석 데이터가 없습니다.")
        return
    
    email_content = generate_email_content(analysis_data)
    subject = f"주식 분석 리포트 - {datetime.now().strftime('%Y년 %m월 %d일')}"
    
    success_count = 0
    for subscriber in subscribers:
        email = subscriber.get('email')
        name = subscriber.get('name', '고객')
        
        if email:
            personalized_content = f"안녕하세요, {name}님!\n\n{email_content}"
            
            if send_email_notification(email, subject, personalized_content):
                success_count += 1
                logging.info(f"이메일 발송 성공: {email}")
            else:
                logging.error(f"이메일 발송 실패: {email}")
    
    logging.info(f"이메일 발송 완료: {success_count}/{len(subscribers)}")

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
        price = stock.get('current_price', 0)
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

get_subscribers_task >> send_daily_emails_task
get_analysis_task >> send_daily_emails_task
get_analysis_task >> send_alert_emails_task
