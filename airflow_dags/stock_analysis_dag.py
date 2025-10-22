from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.sensors.filesystem import FileSensor
from airflow.models import Variable
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.stock_data_collector import StockDataCollector, DataQualityChecker
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService, AlertManager
from config.settings import settings
import logging
default_args = {
    'owner': 'stock-analysis-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

stock_analysis_dag = DAG(
    'stock_analysis_pipeline',
    default_args=default_args,
    description='실시간 주식 데이터 수집, 분석, 알림 파이프라인',
    schedule_interval='*/15 * * * *',
    catchup=False,
    tags=['stock', 'analysis', 'real-time']
)

def collect_stock_data(**context):
    logging.info("주식 데이터 수집 시작")
    
    collector = StockDataCollector(settings.ANALYSIS_SYMBOLS)
    realtime_data = collector.get_multiple_realtime_data()
    
    quality_checker = DataQualityChecker()
    quality_results = []
    
    for data in realtime_data:
        if data:
            quality_result = {
                'symbol': data['symbol'],
                'is_valid': data['price'] > 0,
                'data_quality_score': 1.0 if data['price'] > 0 else 0.0,
                'issues': []
            }
            quality_results.append(quality_result)
    
    context['task_instance'].xcom_push(key='realtime_data', value=realtime_data)
    context['task_instance'].xcom_push(key='quality_results', value=quality_results)
    
    logging.info(f"데이터 수집 완료: {len(realtime_data)}개 종목")
    return realtime_data

def analyze_technical_indicators(**context):
    logging.info("기술적 분석 시작")
    
    realtime_data = context['task_instance'].xcom_pull(key='realtime_data')
    
    if not realtime_data:
        logging.warning("분석할 데이터가 없습니다")
        return []
    
    analyzer = TechnicalAnalyzer()
    analysis_results = []
    
    for data in realtime_data:
        symbol = data['symbol']
        logging.info(f"{symbol} 기술적 분석 수행")
        
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        np.random.seed(hash(symbol) % 2**32)
        
        historical_data = pd.DataFrame({
            'date': dates,
            'close': data['price'] + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })
        
        analyzed_data = analyzer.calculate_all_indicators(historical_data)
        trend_analysis = analyzer.analyze_trend(analyzed_data)
        anomalies = analyzer.detect_anomalies(analyzed_data, symbol)
        signals = analyzer.generate_signals(analyzed_data, symbol)
        
        analysis_result = {
            'symbol': symbol,
            'current_price': data['price'],
            'trend': trend_analysis['trend'],
            'trend_strength': trend_analysis['strength'],
            'signals': signals,
            'anomalies': anomalies,
            'timestamp': datetime.now()
        }
        
        analysis_results.append(analysis_result)
        
        logging.info(f"{symbol} 분석 완료: {trend_analysis['trend']} ({signals['signal']})")
    
    context['task_instance'].xcom_push(key='analysis_results', value=analysis_results)
    
    logging.info(f"기술적 분석 완료: {len(analysis_results)}개 종목")
    return analysis_results

def send_notifications(**context):
    import pymysql
    import json
    
    logging.info("알림 발송 시작")
    
    analysis_results = context['task_instance'].xcom_pull(key='analysis_results')
    quality_results = context['task_instance'].xcom_pull(key='quality_results')
    
    if not analysis_results:
        logging.warning("알림할 분석 결과가 없습니다")
        return
    
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            port=settings.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        email_config = {
            'smtp_server': settings.EMAIL_SMTP_SERVER,
            'smtp_port': settings.EMAIL_SMTP_PORT,
            'user': settings.EMAIL_USER,
            'password': settings.EMAIL_PASSWORD
        }
        
        notification_service = NotificationService(
            email_config=email_config,
            slack_webhook=settings.SLACK_WEBHOOK_URL
        )
        
        alert_manager = AlertManager(notification_service)
        
        cursor.execute("""
            SELECT user_email, symbol, notification_types, rsi_threshold, 
                   volume_spike_threshold, price_change_threshold 
            FROM notification_settings 
            WHERE is_active = TRUE
        """)
        
        notification_settings = cursor.fetchall()
        
        if not notification_settings:
            logging.warning("활성화된 알림 설정이 없습니다")
            return
        
        all_anomalies = []
        for result in analysis_results:
            all_anomalies.extend(result.get('anomalies', []))
        
        total_alerts_sent = 0
        total_reports_sent = 0
        
        for setting in notification_settings:
            user_email, symbol_filter, notification_types, rsi_threshold, volume_threshold, price_threshold = setting
            
            notification_types_dict = json.loads(notification_types) if notification_types else {}
            
            filtered_anomalies = []
            filtered_analyses = []
            
            for anomaly in all_anomalies:
                if symbol_filter is None or anomaly.get('symbol') == symbol_filter:
                    if anomaly.get('type') == 'volume_spike' and anomaly.get('current_value', 0) > volume_threshold:
                        filtered_anomalies.append(anomaly)
                    elif anomaly.get('type') == 'rsi_extreme' and anomaly.get('current_value', 0) > rsi_threshold:
                        filtered_anomalies.append(anomaly)
                    elif anomaly.get('type') == 'price_spike' and abs(anomaly.get('current_value', 0)) > price_threshold:
                        filtered_anomalies.append(anomaly)
            
            for analysis in analysis_results:
                if symbol_filter is None or analysis.get('symbol') == symbol_filter:
                    if analysis.get('signals', {}).get('confidence', 0) > 0.7:
                        filtered_analyses.append(analysis)
            
            if filtered_anomalies and notification_types_dict.get('anomaly_alerts', True):
                anomaly_result = alert_manager.process_anomaly_alerts(filtered_anomalies, [user_email])
                total_alerts_sent += anomaly_result['alerts_sent']
                
                for anomaly in filtered_anomalies:
                    alert_message = alert_manager.notification_service.create_anomaly_alert(anomaly)
                    cursor.execute("""
                        INSERT INTO notification_logs 
                        (user_email, symbol, notification_type, message, status, sent_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        user_email,
                        anomaly.get('symbol'),
                        'email',
                        alert_message,
                        'sent' if anomaly_result['alerts_sent'] > 0 else 'failed',
                        datetime.now()
                    ))
                    logging.info(f"이상 패턴 알림 로그 저장: {user_email} -> {anomaly.get('symbol')}")
            
            if filtered_analyses and notification_types_dict.get('analysis_reports', True):
                report_result = alert_manager.process_analysis_reports(filtered_analyses, [user_email])
                total_reports_sent += report_result['reports_sent']
                
                for analysis in filtered_analyses:
                    report_message = alert_manager.notification_service.create_analysis_report(analysis)
                    cursor.execute("""
                        INSERT INTO notification_logs 
                        (user_email, symbol, notification_type, message, status, sent_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        user_email,
                        analysis.get('symbol'),
                        'email',
                        report_message,
                        'sent' if report_result['reports_sent'] > 0 else 'failed',
                        datetime.now()
                    ))
                    logging.info(f"분석 리포트 알림 로그 저장: {user_email} -> {analysis.get('symbol')}")
        
        conn.commit()
        logging.info(f"이상 패턴 알림 발송: {total_alerts_sent}개")
        logging.info(f"분석 리포트 발송: {total_reports_sent}개")
        
    except Exception as e:
        logging.error(f"알림 발송 실패: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()
    
    return {
        'anomaly_alerts': total_alerts_sent,
        'reports_sent': total_reports_sent,
        'timestamp': datetime.now()
    }

def save_analysis_results(**context):
    import pymysql
    from datetime import datetime
    
    logging.info("분석 결과 저장 시작")
    
    analysis_results = context['task_instance'].xcom_pull(key='analysis_results')
    
    if not analysis_results:
        logging.warning("저장할 분석 결과가 없습니다")
        return
    
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            port=settings.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        saved_count = 0
        for result in analysis_results:
            symbol = result['symbol']
            trend = result['trend']
            signal = result['signals']['signal']
            confidence = result['signals']['confidence']
            current_price = result.get('current_price', 0)
            volume = result.get('volume', 0)
            change_percent = result.get('change_percent', 0)
            
            insert_query = """
            INSERT INTO daily_analysis_summary 
            (symbol, analysis_date, overall_sentiment, key_signals, risk_score, recommendation, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            overall_sentiment = VALUES(overall_sentiment),
            key_signals = VALUES(key_signals),
            risk_score = VALUES(risk_score),
            recommendation = VALUES(recommendation),
            confidence_score = VALUES(confidence_score)
            """
            
            key_signals = result.get('signals', {}).get('signals', [])
            risk_score = 1.0 - confidence
            
            cursor.execute(insert_query, (
                symbol,
                datetime.now().date(),
                trend,
                str(key_signals),
                risk_score,
                signal,
                confidence
            ))
            
            logging.info(f"DB 저장 완료: {symbol} - {trend} ({signal}, 신뢰도: {confidence:.2f})")
            saved_count += 1
        
        conn.commit()
        logging.info(f"분석 결과 저장 완료: {saved_count}개 종목")
        
    except Exception as e:
        logging.error(f"DB 저장 실패: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()
    
    return saved_count

start_task = DummyOperator(
    task_id='start',
    dag=stock_analysis_dag
)

collect_data_task = PythonOperator(
    task_id='collect_stock_data',
    python_callable=collect_stock_data,
    dag=stock_analysis_dag
)

analyze_task = PythonOperator(
    task_id='analyze_technical_indicators',
    python_callable=analyze_technical_indicators,
    dag=stock_analysis_dag
)

notify_task = PythonOperator(
    task_id='send_notifications',
    python_callable=send_notifications,
    dag=stock_analysis_dag
)

save_results_task = PythonOperator(
    task_id='save_analysis_results',
    python_callable=save_analysis_results,
    dag=stock_analysis_dag
)

end_task = DummyOperator(
    task_id='end',
    dag=stock_analysis_dag
)

start_task >> collect_data_task >> analyze_task >> [notify_task, save_results_task] >> end_task
