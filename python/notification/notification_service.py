import smtplib
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.logging_config import get_logger
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = get_logger(__name__)
from exceptions import (
    NotificationError,
    EmailNotificationError,
    SMSNotificationError,
    NetworkError,
    ConnectionError,
    TimeoutError,
    ConfigurationError
)

try:
    from solapi import SolapiMessageService
    from solapi.model import RequestMessage
    SOLAPI_AVAILABLE = True
except ImportError:
    SOLAPI_AVAILABLE = False
    logger.warning("solapi 모듈이 설치되지 않았습니다. 문자 발송 기능이 비활성화됩니다.", component="NotificationService")

class NotificationService:
    
    def __init__(self, email_config: Dict = None, slack_webhook: str = None, solapi_config: Dict = None):
        self.email_config = email_config or {}
        self.slack_webhook = slack_webhook
        self.solapi_config = solapi_config or {}
        self.session = requests.Session()
        
        if SOLAPI_AVAILABLE and self.solapi_config.get('api_key') and self.solapi_config.get('api_secret'):
            try:
                self.message_service = SolapiMessageService(
                    api_key=self.solapi_config['api_key'],
                    api_secret=self.solapi_config['api_secret']
                )
            except (ConfigurationError, ConnectionError) as e:
                logger.error("SOLAPI 초기화 실패", exception=e, component="NotificationService")
                self.message_service = None
            except Exception as e:
                logger.error("SOLAPI 초기화 예상치 못한 오류", exception=e, component="NotificationService")
                self.message_service = None
        else:
            self.message_service = None
        
    def send_email(self, to_email: str, subject: str, body: str, max_retries: int = 3) -> bool:
        try:
            if not self.email_config:
                logger.warning("이메일 설정이 없습니다", component="NotificationService")
                return False
            
            smtp_server = self.email_config.get('smtp_server')
            smtp_port = self.email_config.get('smtp_port', 587)
            user = self.email_config.get('user')
            password = self.email_config.get('password')
            
            if not all([smtp_server, user, password]):
                logger.warning("이메일 설정이 완전하지 않습니다", component="NotificationService")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            last_error = None
            for attempt in range(1, max_retries + 1):
            server = None
            try:
                    if attempt > 1:
                        delay = min(2 ** (attempt - 1), 10)
                        logger.info("이메일 발송 재시도", to_email=to_email, attempt=attempt, delay=delay, component="NotificationService")
                        time.sleep(delay)
                    
                    logger.info("SMTP 서버 연결 시도", to_email=to_email, smtp_server=smtp_server, smtp_port=smtp_port, attempt=attempt, component="NotificationService")
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                    logger.info("SMTP 서버 연결 성공", to_email=to_email, attempt=attempt, component="NotificationService")
                
                    logger.info("STARTTLS 시작", to_email=to_email, attempt=attempt, component="NotificationService")
                server.starttls()
                    logger.info("STARTTLS 완료", to_email=to_email, attempt=attempt, component="NotificationService")
                
                    logger.info("SMTP 로그인 시도", to_email=to_email, user=user, attempt=attempt, component="NotificationService")
                server.login(user, password)
                    logger.info("SMTP 로그인 성공", to_email=to_email, attempt=attempt, component="NotificationService")
                
                    logger.info("이메일 발송 시도", to_email=to_email, subject=subject, attempt=attempt, component="NotificationService")
                failed_recipients = server.send_message(msg)
                    logger.info("send_message 반환값", to_email=to_email, failed_recipients=failed_recipients, attempt=attempt, component="NotificationService")
                
                if failed_recipients:
                    logger.error("이메일 발송 실패: 일부 수신자에게 발송 실패", to_email=to_email, failed_recipients=failed_recipients, component="NotificationService")
                    raise EmailNotificationError(
                        f"이메일 발송 실패: 수신자에게 발송할 수 없습니다. {failed_recipients}",
                        error_code="EMAIL_SEND_FAILED",
                        cause=None
                    )
                
                    logger.info("이메일 발송 성공", to_email=to_email, subject=subject, attempt=attempt, component="NotificationService")
                return True
                except smtplib.SMTPConnectError as e:
                    last_error = e
                    error_msg = str(e)
                    if "Too many concurrent connection" in error_msg or "421" in error_msg:
                        if attempt < max_retries:
                            logger.warning("SMTP 동시 연결 제한 오류, 재시도 예정", to_email=to_email, attempt=attempt, error=error_msg, component="NotificationService")
                            if server:
                                try:
                                    server.quit()
                                except:
                                    pass
                            continue
                        else:
                            logger.error("SMTP 동시 연결 제한 오류, 재시도 한도 초과", to_email=to_email, attempt=attempt, error=error_msg, component="NotificationService")
                            raise EmailNotificationError(
                                f"이메일 SMTP 오류: {error_msg}",
                                error_code="EMAIL_SMTP_ERROR",
                                cause=e
                            ) from e
                    else:
                        raise
            finally:
                if server:
                    try:
                        server.quit()
                            logger.debug("SMTP 서버 연결 종료", to_email=to_email, attempt=attempt, component="NotificationService")
                    except Exception as e:
                        logger.warning("SMTP 서버 종료 중 오류 발생 (무시됨)", exception=e, component="NotificationService")
            
            if last_error:
                raise last_error
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error("이메일 인증 실패", to_email=to_email, exception=e, component="NotificationService")
            raise EmailNotificationError(
                f"이메일 인증 실패: {str(e)}",
                error_code="EMAIL_AUTH_FAILED",
                cause=e
            ) from e
        except smtplib.SMTPException as e:
            logger.error("이메일 SMTP 오류", to_email=to_email, exception=e, component="NotificationService")
            raise EmailNotificationError(
                f"이메일 SMTP 오류: {str(e)}",
                error_code="EMAIL_SMTP_ERROR",
                cause=e
            ) from e
        except (ConnectionError, TimeoutError) as e:
            logger.error("이메일 네트워크 오류", to_email=to_email, exception=e, component="NotificationService")
            raise EmailNotificationError(
                f"이메일 네트워크 오류: {str(e)}",
                error_code="EMAIL_NETWORK_ERROR",
                cause=e
            ) from e
        except ConfigurationError as e:
            logger.error("이메일 설정 오류", to_email=to_email, exception=e, component="NotificationService")
            raise EmailNotificationError(
                f"이메일 설정 오류: {str(e)}",
                error_code="EMAIL_CONFIG_ERROR",
                cause=e
            ) from e
        except Exception as e:
            logger.error("이메일 발송 예상치 못한 오류", to_email=to_email, exception=e, component="NotificationService")
            raise EmailNotificationError(
                f"이메일 발송 실패: {str(e)}",
                error_code="EMAIL_SEND_FAILED",
                cause=e
            ) from e
    
    def send_slack_message(self, message: str) -> bool:
        try:
            if not self.slack_webhook:
                return False
            
            payload = {
                'text': message,
                'username': 'Stock Analyzer Bot'
            }
            
            response = self.session.post(self.slack_webhook, json=payload)
            response.raise_for_status()
            
            logger.info("Slack 메시지 발송 성공", component="NotificationService")
            return True
            
        except (ConnectionError, TimeoutError) as e:
            logger.error("Slack 메시지 네트워크 오류", exception=e, component="NotificationService")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error("Slack 메시지 HTTP 오류", exception=e, component="NotificationService")
            return False
        except Exception as e:
            logger.error("Slack 메시지 발송 예상치 못한 오류", exception=e, component="NotificationService")
            return False
    
    def send_telegram_message(self, bot_token: str, chat_id: str, message: str) -> bool:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            logger.info("Telegram 메시지 발송 성공", component="NotificationService")
            return True
            
        except Exception as e:
            logger.error("Telegram 메시지 발송 실패", exception=e, component="NotificationService")
            return False
    
    def send_sms(self, from_phone: str, to_phone: str, message: str) -> bool:
        try:
            if not SOLAPI_AVAILABLE:
                logger.warning("solapi 모듈이 설치되지 않았습니다", component="NotificationService")
                return False
            
            if not self.message_service:
                logger.warning("SOLAPI 서비스가 초기화되지 않았습니다", component="NotificationService")
                return False
            
            from_phone = from_phone.replace("-", "").replace(" ", "")
            to_phone = to_phone.replace("-", "").replace(" ", "")
            
            sms_message = RequestMessage(
                from_=from_phone,
                to=to_phone,
                text=message
            )
            
            response = self.message_service.send(sms_message)
            
            if response and response.group_info:
                success_count = response.group_info.count.registered_success
                failed_count = response.group_info.count.registered_failed
                
                if success_count > 0:
                    logger.info("SMS 발송 성공", 
                              to_phone=to_phone, 
                              group_id=response.group_info.group_id, 
                              component="NotificationService")
                    return True
                else:
                    logger.error("SMS 발송 실패", to_phone=to_phone, failed_count=failed_count, component="NotificationService")
                    return False
            else:
                logger.error("SMS 발송 실패: 응답 형식 오류", to_phone=to_phone, component="NotificationService")
                return False
                
        except Exception as e:
            logger.error("SMS 발송 실패", to_phone=to_phone, exception=e, component="NotificationService")
            return False
    
    def create_anomaly_alert(self, anomaly_data: Dict) -> str:
        symbol = anomaly_data.get('symbol', 'N/A')
        anomaly_type = anomaly_data.get('type', 'unknown')
        severity = anomaly_data.get('severity', 'medium').upper()
        message = anomaly_data.get('message', '이상 패턴 감지')
        
        alert = f"""
{symbol} 이상 패턴 감지

타입: {anomaly_type}
심각도: {severity}
메시지: {message}

발생 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return alert
    
    def create_analysis_report(self, analysis_data: Dict) -> str:
        symbol = analysis_data.get('symbol', 'N/A')
        trend = analysis_data.get('trend', 'neutral').upper()
        confidence = analysis_data.get('confidence', 0.0) * 100
        signals = analysis_data.get('signals', [])
        
        if isinstance(signals, dict):
            signals = signals.get('signals', [])
        if not isinstance(signals, list):
            signals = []
        
        report = f"""
{symbol} 분석 리포트

트렌드: {trend}
신뢰도: {confidence:.1f}%

주요 신호:
"""
        for signal in signals:
            report += f"  - {signal}\n"
        
        report += f"\n생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    def send_bulk_notifications(self, notifications: List[Dict]) -> Dict:
        email_success = 0
        email_failed = 0
        slack_success = 0
        slack_failed = 0
        
        for notification in notifications:
            notification_type = notification.get('type', 'email')
            
            if notification_type == 'email':
                result = self.send_email(
                    to_email=notification.get('recipient', ''),
                    subject=notification.get('subject', ''),
                    body=notification.get('content', '')
                )
                if result:
                    email_success += 1
                else:
                    email_failed += 1
                    
            elif notification_type == 'slack':
                result = self.send_slack_message(notification.get('content', ''))
                if result:
                    slack_success += 1
                else:
                    slack_failed += 1
        
        return {
            'email_success': email_success,
            'email_failed': email_failed,
            'slack_success': slack_success,
            'slack_failed': slack_failed,
            'total_sent': email_success + slack_success
        }

class AlertManager:
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.alert_history = []
    
    def process_anomaly_alerts(self, anomalies: List[Dict], recipients: List[str]) -> Dict:
        alerts_sent = 0
        anomalies_processed = len(anomalies)
        
        high_severity_anomalies = [a for a in anomalies if a.get('severity') == 'high']
        
        if not high_severity_anomalies:
            return {
                'alerts_sent': 0,
                'anomalies_processed': anomalies_processed,
                'timestamp': datetime.now()
            }
        
        for anomaly in high_severity_anomalies:
            alert_message = self.notification_service.create_anomaly_alert(anomaly)
            
            for recipient in recipients:
                if self.notification_service.send_email(
                    to_email=recipient,
                    subject=f"{anomaly.get('symbol', 'N/A')} 이상 패턴 알림",
                    body=alert_message
                ):
                    alerts_sent += 1
        
        alert_record = {
            'timestamp': datetime.now(),
            'type': 'anomaly',
            'anomalies': high_severity_anomalies,
            'alerts_sent': alerts_sent
        }
        self.alert_history.append(alert_record)
        
        return {
            'alerts_sent': alerts_sent,
            'anomalies_processed': anomalies_processed,
            'timestamp': datetime.now()
        }
    
    def process_analysis_reports(self, analyses: List[Dict], recipients: List[str]) -> Dict:
        reports_sent = 0
        analyses_processed = len(analyses)
        
        high_confidence_analyses = [a for a in analyses if a.get('confidence', 0) > 0.7]
        
        if not high_confidence_analyses:
            return {
                'reports_sent': 0,
                'analyses_processed': analyses_processed,
                'timestamp': datetime.now()
            }
        
        for analysis in high_confidence_analyses:
            report_message = self.notification_service.create_analysis_report(analysis)
            
            for recipient in recipients:
                if self.notification_service.send_email(
                    to_email=recipient,
                    subject=f"{analysis.get('symbol', 'N/A')} 분석 리포트",
                    body=report_message
                ):
                    reports_sent += 1
        
        return {
            'reports_sent': reports_sent,
            'analyses_processed': analyses_processed,
            'timestamp': datetime.now()
        }
    
    def get_alert_summary(self, hours: int = 24) -> Dict:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alert_history if a['timestamp'] >= cutoff_time]
        
        severity_breakdown = {}
        symbol_breakdown = {}
        
        for alert in recent_alerts:
            if alert['type'] == 'anomaly':
                for anomaly in alert.get('anomalies', []):
                    severity = anomaly.get('severity', 'medium')
                    symbol = anomaly.get('symbol', 'N/A')
                    
                    severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
                    symbol_breakdown[symbol] = symbol_breakdown.get(symbol, 0) + 1
        
        return {
            'total_alerts': len(recent_alerts),
            'severity_breakdown': severity_breakdown,
            'symbol_breakdown': symbol_breakdown
        }

