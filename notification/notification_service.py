import smtplib
import requests
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import aiohttp

class NotificationService:
    
    def __init__(self, email_config: Dict, slack_webhook: str = None):
        self.email_config = email_config
        self.slack_webhook = slack_webhook
        self.session = requests.Session()
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['user']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['user'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['user'], to_email, text)
            server.quit()
            
            logging.info(f"이메일 발송 성공: {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"이메일 발송 실패: {str(e)}")
            return False
    
    def send_slack_message(self, message: str, channel: str = None) -> bool:
        if not self.slack_webhook:
            logging.warning("슬랙 웹훅 URL이 설정되지 않았습니다")
            return False
        
        try:
            payload = {
                'text': message,
                'username': 'Stock Analyzer Bot'
            }
            
            if channel:
                payload['channel'] = channel
            
            response = self.session.post(self.slack_webhook, json=payload)
            response.raise_for_status()
            
            logging.info("슬랙 메시지 발송 성공")
            return True
            
        except Exception as e:
            logging.error(f"슬랙 메시지 발송 실패: {str(e)}")
            return False
    
    def send_telegram_message(self, bot_token: str, chat_id: str, message: str) -> bool:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            logging.info("텔레그램 메시지 발송 성공")
            return True
            
        except Exception as e:
            logging.error(f"텔레그램 메시지 발송 실패: {str(e)}")
            return False
    
    def create_anomaly_alert(self, anomaly_data: Dict) -> str:
        symbol = anomaly_data.get('symbol', 'Unknown')
        anomaly_type = anomaly_data.get('type', 'unknown')
        message = anomaly_data.get('message', '')
        severity = anomaly_data.get('severity', 'medium')
        
        alert_message = f"""
{symbol} 이상 패턴 감지

유형: {anomaly_type}
심각도: {severity.upper()}
내용: {message}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return alert_message
    
    def create_analysis_report(self, analysis_data: Dict) -> str:
        symbol = analysis_data.get('symbol', 'Unknown')
        trend = analysis_data.get('trend', 'unknown')
        signals = analysis_data.get('signals', [])
        confidence = analysis_data.get('confidence', 0)
        
        report = f"""
{symbol} 분석 리포트

트렌드: {trend.upper()}
신뢰도: {confidence:.1%}
주요 신호:
        """.strip()
        
        for signal in signals[:5]:
            report += f"\n  • {signal}"
        
        report += f"\n\n분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return report
    
    def send_bulk_notifications(self, notifications: List[Dict]) -> Dict:
        results = {
            'email_success': 0,
            'email_failed': 0,
            'slack_success': 0,
            'slack_failed': 0,
            'total_sent': 0
        }
        
        for notification in notifications:
            notification_type = notification.get('type', 'email')
            content = notification.get('content', '')
            recipient = notification.get('recipient', '')
            
            success = False
            
            if notification_type == 'email':
                success = self.send_email(
                    to_email=recipient,
                    subject=notification.get('subject', 'Stock Analysis Alert'),
                    body=content,
                    is_html=notification.get('is_html', False)
                )
                if success:
                    results['email_success'] += 1
                else:
                    results['email_failed'] += 1
                    
            elif notification_type == 'slack':
                success = self.send_slack_message(content)
                if success:
                    results['slack_success'] += 1
                else:
                    results['slack_failed'] += 1
            
            if success:
                results['total_sent'] += 1
        
        return results

class AlertManager:
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.alert_history = []
    
    def process_anomaly_alerts(self, anomalies: List[Dict], recipients: List[str]) -> Dict:
        alerts_sent = 0
        
        for anomaly in anomalies:
            if anomaly.get('severity') in ['high', 'medium']:
                alert_message = self.notification_service.create_anomaly_alert(anomaly)
                
                for recipient in recipients:
                    success = self.notification_service.send_email(
                        to_email=recipient,
                        subject=f"{anomaly.get('symbol', 'Stock')} 이상 패턴 감지",
                        body=alert_message
                    )
                    if success:
                        alerts_sent += 1
                
                self.notification_service.send_slack_message(alert_message)
                
                self.alert_history.append({
                    'timestamp': datetime.now(),
                    'type': 'anomaly',
                    'symbol': anomaly.get('symbol'),
                    'severity': anomaly.get('severity'),
                    'message': alert_message
                })
        
        return {
            'alerts_sent': alerts_sent,
            'anomalies_processed': len(anomalies),
            'timestamp': datetime.now()
        }
    
    def process_analysis_reports(self, analyses: List[Dict], recipients: List[str]) -> Dict:
        reports_sent = 0
        
        for analysis in analyses:
            if analysis.get('confidence', 0) > 0.7:
                report_message = self.notification_service.create_analysis_report(analysis)
                
                for recipient in recipients:
                    success = self.notification_service.send_email(
                        to_email=recipient,
                        subject=f"{analysis.get('symbol', 'Stock')} 분석 리포트",
                        body=report_message
                    )
                    if success:
                        reports_sent += 1
                
                self.notification_service.send_slack_message(report_message)
        
        return {
            'reports_sent': reports_sent,
            'analyses_processed': len(analyses),
            'timestamp': datetime.now()
        }
    
    def get_alert_summary(self, hours: int = 24) -> Dict:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alert_history 
            if alert['timestamp'] > cutoff_time
        ]
        
        severity_counts = {}
        symbol_counts = {}
        
        for alert in recent_alerts:
            severity = alert.get('severity', 'unknown')
            symbol = alert.get('symbol', 'unknown')
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        return {
            'total_alerts': len(recent_alerts),
            'severity_breakdown': severity_counts,
            'symbol_breakdown': symbol_counts,
            'time_range': f"최근 {hours}시간"
        }

if __name__ == "__main__":
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'user': 'your_email@gmail.com',
        'password': 'your_app_password'
    }
    
    notification_service = NotificationService(
        email_config=email_config,
        slack_webhook="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    )
    
    test_anomaly = {
        'symbol': 'AAPL',
        'type': 'volume_spike',
        'severity': 'high',
        'message': 'AAPL: 거래량 급증 (5,000,000 vs 평균 2,000,000)'
    }
    
    alert_message = notification_service.create_anomaly_alert(test_anomaly)
    print("이상 패턴 알림")
    print(alert_message)
    
    test_analysis = {
        'symbol': 'GOOGL',
        'trend': 'bullish',
        'confidence': 0.85,
        'signals': ['RSI 과매도 - 매수 신호', 'MACD 골든크로스 - 매수 신호']
    }
    
    report_message = notification_service.create_analysis_report(test_analysis)
    print("\n분석 리포트")
    print(report_message)
