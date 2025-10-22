import pytest
from unittest.mock import Mock, patch, MagicMock
import smtplib
import requests
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notification.notification_service import NotificationService, AlertManager

class TestNotificationService:
    
    @pytest.fixture
    def email_config(self):
        return {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'user': 'test@gmail.com',
            'password': 'test_password'
        }
    
    @pytest.fixture
    def notification_service(self, email_config):
        return NotificationService(
            email_config=email_config,
            slack_webhook="https://hooks.slack.com/services/test/webhook"
        )
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, notification_service):
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = notification_service.send_email(
            to_email='recipient@example.com',
            subject='Test Subject',
            body='Test Body'
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@gmail.com', 'test_password')
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp, notification_service):
        mock_smtp.side_effect = Exception("SMTP Error")
        
        result = notification_service.send_email(
            to_email='recipient@example.com',
            subject='Test Subject',
            body='Test Body'
        )
        
        assert result is False
    
    @patch('requests.Session.post')
    def test_send_slack_message_success(self, mock_post, notification_service):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = notification_service.send_slack_message("Test message")
        
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['text'] == "Test message"
        assert call_args[1]['json']['username'] == "Stock Analyzer Bot"
    
    @patch('requests.Session.post')
    def test_send_slack_message_failure(self, mock_post, notification_service):
        mock_post.side_effect = Exception("Request Error")
        
        result = notification_service.send_slack_message("Test message")
        
        assert result is False
    
    def test_send_slack_message_no_webhook(self):
        service = NotificationService(email_config={})
        
        result = service.send_slack_message("Test message")
        
        assert result is False
    
    @patch('requests.Session.post')
    def test_send_telegram_message_success(self, mock_post, notification_service):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = notification_service.send_telegram_message(
            bot_token="test_token",
            chat_id="test_chat",
            message="Test message"
        )
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_send_telegram_message_failure(self, mock_post, notification_service):
        mock_post.side_effect = Exception("Request Error")
        
        result = notification_service.send_telegram_message(
            bot_token="test_token",
            chat_id="test_chat",
            message="Test message"
        )
        
        assert result is False
    
    def test_create_anomaly_alert(self, notification_service):
        anomaly_data = {
            'symbol': 'AAPL',
            'type': 'volume_spike',
            'severity': 'high',
            'message': 'AAPL: 거래량 급증'
        }
        
        alert_message = notification_service.create_anomaly_alert(anomaly_data)
        
        assert 'AAPL 이상 패턴 감지' in alert_message
        assert 'volume_spike' in alert_message
        assert 'HIGH' in alert_message
        assert 'AAPL: 거래량 급증' in alert_message
    
    def test_create_analysis_report(self, notification_service):
        analysis_data = {
            'symbol': 'GOOGL',
            'trend': 'bullish',
            'confidence': 0.85,
            'signals': ['RSI 과매도 - 매수 신호', 'MACD 골든크로스 - 매수 신호']
        }
        
        report_message = notification_service.create_analysis_report(analysis_data)
        
        assert 'GOOGL 분석 리포트' in report_message
        assert 'BULLISH' in report_message
        assert '85.0%' in report_message
        assert 'RSI 과매도 - 매수 신호' in report_message
        assert 'MACD 골든크로스 - 매수 신호' in report_message
    
    @patch.object(NotificationService, 'send_email')
    @patch.object(NotificationService, 'send_slack_message')
    def test_send_bulk_notifications(self, mock_slack, mock_email, notification_service):
        mock_email.return_value = True
        mock_slack.return_value = True
        
        notifications = [
            {
                'type': 'email',
                'recipient': 'test@example.com',
                'subject': 'Test Subject',
                'content': 'Test Content'
            },
            {
                'type': 'slack',
                'content': 'Slack Message'
            }
        ]
        
        result = notification_service.send_bulk_notifications(notifications)
        
        assert result['email_success'] == 1
        assert result['slack_success'] == 1
        assert result['total_sent'] == 2
        assert result['email_failed'] == 0
        assert result['slack_failed'] == 0

class TestAlertManager:
    
    @pytest.fixture
    def mock_notification_service(self):
        service = Mock()
        service.create_anomaly_alert.return_value = "Test anomaly alert"
        service.create_analysis_report.return_value = "Test analysis report"
        service.send_email.return_value = True
        service.send_slack_message.return_value = True
        return service
    
    @pytest.fixture
    def alert_manager(self, mock_notification_service):
        return AlertManager(mock_notification_service)
    
    def test_process_anomaly_alerts(self, alert_manager):
        anomalies = [
            {
                'symbol': 'AAPL',
                'severity': 'high',
                'type': 'volume_spike',
                'message': 'AAPL: 거래량 급증'
            },
            {
                'symbol': 'GOOGL',
                'severity': 'low',
                'type': 'price_spike',
                'message': 'GOOGL: 가격 변동'
            }
        ]
        
        recipients = ['analyst@company.com', 'trader@company.com']
        
        result = alert_manager.process_anomaly_alerts(anomalies, recipients)
        
        assert result['alerts_sent'] > 0
        assert result['anomalies_processed'] == 2
        assert 'timestamp' in result
        
        assert len(alert_manager.alert_history) == 1
    
    def test_process_anomaly_alerts_no_high_severity(self, alert_manager):
        anomalies = [
            {
                'symbol': 'AAPL',
                'severity': 'low',
                'type': 'price_spike',
                'message': 'AAPL: 가격 변동'
            }
        ]
        
        recipients = ['analyst@company.com']
        
        result = alert_manager.process_anomaly_alerts(anomalies, recipients)
        
        assert result['alerts_sent'] == 0
        assert result['anomalies_processed'] == 1
        assert len(alert_manager.alert_history) == 0
    
    def test_process_analysis_reports(self, alert_manager):
        analyses = [
            {
                'symbol': 'AAPL',
                'confidence': 0.85,
                'trend': 'bullish'
            },
            {
                'symbol': 'GOOGL',
                'confidence': 0.5,
                'trend': 'neutral'
            }
        ]
        
        recipients = ['analyst@company.com']
        
        result = alert_manager.process_analysis_reports(analyses, recipients)
        
        assert result['reports_sent'] == 1
        assert result['analyses_processed'] == 2
        assert 'timestamp' in result
    
    def test_process_analysis_reports_low_confidence(self, alert_manager):
        analyses = [
            {
                'symbol': 'AAPL',
                'confidence': 0.5,
                'trend': 'neutral'
            }
        ]
        
        recipients = ['analyst@company.com']
        
        result = alert_manager.process_analysis_reports(analyses, recipients)
        
        assert result['reports_sent'] == 0
        assert result['analyses_processed'] == 1
    
    def test_get_alert_summary(self, alert_manager):
        alert_manager.alert_history = [
            {
                'timestamp': datetime.now(),
                'type': 'anomaly',
                'symbol': 'AAPL',
                'severity': 'high',
                'message': 'Test alert 1'
            },
            {
                'timestamp': datetime.now(),
                'type': 'anomaly',
                'symbol': 'GOOGL',
                'severity': 'medium',
                'message': 'Test alert 2'
            }
        ]
        
        summary = alert_manager.get_alert_summary(hours=24)
        
        assert summary['total_alerts'] == 2
        assert 'severity_breakdown' in summary
        assert 'symbol_breakdown' in summary
        assert summary['severity_breakdown']['high'] == 1
        assert summary['severity_breakdown']['medium'] == 1
        assert summary['symbol_breakdown']['AAPL'] == 1
        assert summary['symbol_breakdown']['GOOGL'] == 1
    
    def test_get_alert_summary_empty_history(self, alert_manager):
        alert_manager.alert_history = []
        
        summary = alert_manager.get_alert_summary(hours=24)
        
        assert summary['total_alerts'] == 0
        assert summary['severity_breakdown'] == {}
        assert summary['symbol_breakdown'] == {}
    
    def test_get_alert_summary_time_filter(self, alert_manager):
        from datetime import timedelta
        
        old_alert = {
            'timestamp': datetime.now() - timedelta(hours=25),
            'type': 'anomaly',
            'symbol': 'AAPL',
            'severity': 'high',
            'message': 'Old alert'
        }
        
        recent_alert = {
            'timestamp': datetime.now(),
            'type': 'anomaly',
            'symbol': 'GOOGL',
            'severity': 'medium',
            'message': 'Recent alert'
        }
        
        alert_manager.alert_history = [old_alert, recent_alert]
        
        summary = alert_manager.get_alert_summary(hours=24)
        
        assert summary['total_alerts'] == 1
        assert summary['symbol_breakdown']['GOOGL'] == 1
        assert 'AAPL' not in summary['symbol_breakdown']
