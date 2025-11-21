import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.stock_data_collector import StockDataCollector, DataQualityChecker
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService, AlertManager
from api_server import app, StockAnalysisAPI, ConnectionManager
from fastapi.testclient import TestClient

class TestAdvancedDataCollector:
    
    @pytest.fixture
    def collector(self):
        return StockDataCollector(['AAPL', 'GOOGL'], use_mock_data=True, use_alpha_vantage=True)
    
    def test_alpha_vantage_search_symbols(self, collector):
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'bestMatches': [
                    {'1. symbol': 'AAPL', '2. name': 'Apple Inc.'},
                    {'1. symbol': 'AAPL.US', '2. name': 'Apple Inc. US'}
                ]
            }
            mock_get.return_value = mock_response
            
            result = collector.search_alpha_vantage_symbols('Apple')
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert 'AAPL' in [item['symbol'] for item in result]
    
    def test_alpha_vantage_search_symbols_error(self, collector):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = collector.search_alpha_vantage_symbols('Apple')
            
            assert result == []
    
    def test_alpha_vantage_intraday_data(self, collector):
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'Time Series (5min)': {
                    '2024-01-01 09:30:00': {
                        '1. open': '150.00',
                        '2. high': '151.00',
                        '3. low': '149.00',
                        '4. close': '150.50',
                        '5. volume': '1000000'
                    }
                }
            }
            mock_get.return_value = mock_response
            
            result = collector.get_alpha_vantage_intraday_data('AAPL')
            
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert 'close' in result.columns
    
    def test_alpha_vantage_weekly_data(self, collector):
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'Weekly Time Series': {
                    '2024-01-05': {
                        '1. open': '150.00',
                        '2. high': '155.00',
                        '3. low': '148.00',
                        '4. close': '152.00',
                        '5. volume': '5000000'
                    }
                }
            }
            mock_get.return_value = mock_response
            
            result = collector.get_alpha_vantage_weekly_data('AAPL')
            
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
    
    def test_alpha_vantage_monthly_data(self, collector):
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'Monthly Time Series': {
                    '2024-01-31': {
                        '1. open': '150.00',
                        '2. high': '160.00',
                        '3. low': '145.00',
                        '4. close': '158.00',
                        '5. volume': '20000000'
                    }
                }
            }
            mock_get.return_value = mock_response
            
            result = collector.get_alpha_vantage_monthly_data('AAPL')
            
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
    
    def test_get_alpha_vantage_data_with_api_key(self, collector):
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'Global Quote': {
                    '01. symbol': 'AAPL',
                    '05. price': '150.25',
                    '09. change': '2.50',
                    '10. change percent': '1.69%',
                    '06. volume': '1000000'
                }
            }
            mock_get.return_value = mock_response
            
            result = collector.get_alpha_vantage_data('AAPL', 'test_api_key')
            
            assert result['symbol'] == 'AAPL'
            assert result['price'] == 150.25
            assert result['change'] == 2.50
    
    def test_get_alpha_vantage_data_error(self, collector):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = collector.get_alpha_vantage_data('AAPL', 'test_api_key')
            
            assert result is None
    
    def test_get_alpha_vantage_data_invalid_response(self, collector):
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {'Error Message': 'Invalid API call'}
            mock_get.return_value = mock_response
            
            result = collector.get_alpha_vantage_data('AAPL', 'test_api_key')
            
            assert result is None
    
    def test_collect_batch_data_with_errors(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.side_effect = [Exception("Error"), pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=10, freq='D'),
                'close': np.random.randn(10) * 2 + 100,
                'volume': np.random.randint(1000000, 5000000, 10)
            })]
            
            result = collector.collect_batch_data()
            
            assert isinstance(result, dict)
            assert len(result) == 1
    
    def test_get_multiple_realtime_data_with_errors(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.side_effect = [Exception("Error"), {
                'symbol': 'GOOGL',
                'price': 2500.0,
                'volume': 1000000,
                'timestamp': datetime.now()
            }]
            
            result = collector.get_multiple_realtime_data()
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]['symbol'] == 'GOOGL'

class TestAdvancedTechnicalAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        return TechnicalAnalyzer()
    
    def test_calculate_rsi_with_insufficient_data(self, analyzer):
        insufficient_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5, freq='D'),
            'close': [100, 101, 102, 103, 104]
        })
        
        rsi = analyzer.calculate_rsi(insufficient_data)
        
        assert rsi.empty
    
    def test_calculate_macd_with_insufficient_data(self, analyzer):
        insufficient_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5, freq='D'),
            'close': [100, 101, 102, 103, 104]
        })
        
        macd_data = analyzer.calculate_macd(insufficient_data)
        
        assert macd_data['macd'].empty
        assert macd_data['macd_signal'].empty
        assert macd_data['macd_histogram'].empty
    
    def test_calculate_bollinger_bands_with_insufficient_data(self, analyzer):
        insufficient_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5, freq='D'),
            'close': [100, 101, 102, 103, 104]
        })
        
        bb_data = analyzer.calculate_bollinger_bands(insufficient_data)
        
        assert bb_data['bb_upper'].empty
        assert bb_data['bb_middle'].empty
        assert bb_data['bb_lower'].empty
    
    def test_calculate_moving_averages_with_insufficient_data(self, analyzer):
        insufficient_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5, freq='D'),
            'close': [100, 101, 102, 103, 104]
        })
        
        ma_data = analyzer.calculate_moving_averages(insufficient_data)
        
        assert ma_data['sma_20'].empty
        assert ma_data['sma_50'].empty
        assert ma_data['ema_12'].empty
        assert ma_data['ema_26'].empty
    
    def test_analyze_trend_with_extreme_rsi(self, analyzer):
        extreme_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100] * 30,
            'volume': [1000] * 30,
            'rsi_14': [90] * 30
        })
        
        trend_analysis = analyzer.analyze_trend(extreme_data)
        
        assert trend_analysis['trend'] in ['bullish', 'bearish', 'neutral']
        assert 0 <= trend_analysis['strength'] <= 1
    
    def test_detect_anomalies_with_extreme_volume(self, analyzer):
        extreme_volume_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100] * 30,
            'volume': [1000] * 29 + [10000000]
        })
        
        analyzed_data = analyzer.calculate_all_indicators(extreme_volume_data)
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        
        volume_anomalies = [a for a in anomalies if a['type'] == 'volume_spike']
        assert len(volume_anomalies) > 0
    
    def test_detect_anomalies_with_extreme_price(self, analyzer):
        extreme_price_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100] * 29 + [200],
            'volume': [1000] * 30
        })
        
        analyzed_data = analyzer.calculate_all_indicators(extreme_price_data)
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        
        price_anomalies = [a for a in anomalies if a['type'] == 'price_spike']
        assert len(price_anomalies) > 0
    
    def test_generate_signals_with_mixed_indicators(self, analyzer):
        mixed_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100 + i for i in range(30)],
            'volume': [1000 + i * 100 for i in range(30)],
            'rsi_14': [30 + i for i in range(30)],
            'macd': [0.1 + i * 0.01 for i in range(30)],
            'macd_signal': [0.1 + i * 0.01 for i in range(30)]
        })
        
        signals = analyzer.generate_signals(mixed_data, 'TEST')
        
        assert signals['signal'] in ['buy', 'sell', 'hold']
        assert 0 <= signals['confidence'] <= 1
        assert isinstance(signals['signals'], list)
        assert isinstance(signals['reason'], str)
    
    def test_calculate_all_indicators_with_missing_columns(self, analyzer):
        incomplete_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100 + i for i in range(30)]
        })
        
        result = analyzer.calculate_all_indicators(incomplete_data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'close' in result.columns

class TestAdvancedNotificationService:
    
    @pytest.fixture
    def notification_service(self):
        return NotificationService(
            email_config={
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'user': 'test@gmail.com',
                'password': 'test_password'
            },
            slack_webhook="https://hooks.slack.com/services/test/webhook"
        )
    
    def test_send_email_with_ssl_error(self, notification_service):
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_server.starttls.side_effect = Exception("SSL Error")
            mock_smtp.return_value = mock_server
            
            result = notification_service.send_email(
                to_email='test@example.com',
                subject='Test',
                body='Test'
            )
            
            assert result is False
    
    def test_send_email_with_login_error(self, notification_service):
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_server.login.side_effect = Exception("Login Error")
            mock_smtp.return_value = mock_server
            
            result = notification_service.send_email(
                to_email='test@example.com',
                subject='Test',
                body='Test'
            )
            
            assert result is False
    
    def test_send_email_with_sendmail_error(self, notification_service):
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_server.sendmail.side_effect = Exception("Sendmail Error")
            mock_smtp.return_value = mock_server
            
            result = notification_service.send_email(
                to_email='test@example.com',
                subject='Test',
                body='Test'
            )
            
            assert result is False
    
    def test_send_slack_message_with_http_error(self, notification_service):
        with patch('requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP Error")
            mock_post.return_value = mock_response
            
            result = notification_service.send_slack_message("Test message")
            
            assert result is False
    
    def test_send_telegram_message_with_http_error(self, notification_service):
        with patch('requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP Error")
            mock_post.return_value = mock_response
            
            result = notification_service.send_telegram_message(
                bot_token="test_token",
                chat_id="test_chat",
                message="Test message"
            )
            
            assert result is False
    
    def test_send_bulk_notifications_with_mixed_results(self, notification_service):
        with patch.object(notification_service, 'send_email') as mock_email:
            with patch.object(notification_service, 'send_slack_message') as mock_slack:
                mock_email.return_value = True
                mock_slack.return_value = False
                
                notifications = [
                    {'type': 'email', 'recipient': 'test@example.com', 'subject': 'Test', 'content': 'Test'},
                    {'type': 'slack', 'content': 'Test message'},
                    {'type': 'email', 'recipient': 'test2@example.com', 'subject': 'Test2', 'content': 'Test2'}
                ]
                
                result = notification_service.send_bulk_notifications(notifications)
                
                assert result['email_success'] == 2
                assert result['slack_success'] == 0
                assert result['email_failed'] == 0
                assert result['slack_failed'] == 1
                assert result['total_sent'] == 2

class TestAdvancedAlertManager:
    
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
    
    def test_process_anomaly_alerts_with_email_failure(self, alert_manager):
        alert_manager.notification_service.send_email.return_value = False
        
        anomalies = [
            {
                'symbol': 'AAPL',
                'severity': 'high',
                'type': 'volume_spike',
                'message': 'AAPL: 거래량 급증'
            }
        ]
        
        recipients = ['analyst@company.com']
        
        result = alert_manager.process_anomaly_alerts(anomalies, recipients)
        
        assert result['alerts_sent'] == 0
        assert result['anomalies_processed'] == 1
    
    def test_process_analysis_reports_with_email_failure(self, alert_manager):
        alert_manager.notification_service.send_email.return_value = False
        
        analyses = [
            {
                'symbol': 'AAPL',
                'confidence': 0.85,
                'trend': 'bullish'
            }
        ]
        
        recipients = ['analyst@company.com']
        
        result = alert_manager.process_analysis_reports(analyses, recipients)
        
        assert result['reports_sent'] == 0
        assert result['analyses_processed'] == 1
    
    def test_get_alert_summary_with_different_types(self, alert_manager):
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
                'type': 'analysis',
                'symbol': 'GOOGL',
                'severity': 'medium',
                'message': 'Test alert 2'
            }
        ]
        
        summary = alert_manager.get_alert_summary(hours=24)
        
        assert summary['total_alerts'] == 2
        assert 'type_breakdown' in summary
        assert summary['type_breakdown']['anomaly'] == 1
        assert summary['type_breakdown']['analysis'] == 1

class TestAdvancedAPI:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_connection_manager(self):
        manager = ConnectionManager()
        
        assert len(manager.active_connections) == 0
        
        mock_websocket = Mock()
        manager.active_connections.append(mock_websocket)
        
        assert len(manager.active_connections) == 1
        
        manager.disconnect(mock_websocket)
        assert len(manager.active_connections) == 0
    
    def test_connection_manager_broadcast_error(self):
        manager = ConnectionManager()
        
        mock_websocket1 = Mock()
        mock_websocket2 = Mock()
        mock_websocket2.send_text.side_effect = Exception("Send error")
        
        manager.active_connections = [mock_websocket1, mock_websocket2]
        
        manager.broadcast("test message")
        
        assert len(manager.active_connections) == 1
        assert mock_websocket1 in manager.active_connections
        assert mock_websocket2 not in manager.active_connections
    
    @patch('api_server.stock_api.collector.search_alpha_vantage_symbols')
    def test_search_symbols_endpoint(self, mock_search, client):
        mock_search.return_value = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.'}
        ]
        
        response = client.get("/api/alpha-vantage/search/Apple")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['symbol'] == 'AAPL'
    
    @patch('api_server.stock_api.collector.get_alpha_vantage_intraday_data')
    def test_alpha_vantage_intraday_endpoint(self, mock_intraday, client):
        mock_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=10, freq='5min'),
            'close': [100 + i for i in range(10)],
            'volume': [1000 + i * 100 for i in range(10)]
        })
        mock_intraday.return_value = mock_data
        
        response = client.get("/api/alpha-vantage/intraday/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
    
    @patch('api_server.stock_api.collector.get_alpha_vantage_intraday_data')
    def test_alpha_vantage_intraday_not_found(self, mock_intraday, client):
        mock_intraday.return_value = pd.DataFrame()
        
        response = client.get("/api/alpha-vantage/intraday/INVALID")
        assert response.status_code == 404
    
    @patch('api_server.stock_api.collector.get_alpha_vantage_weekly_data')
    def test_alpha_vantage_weekly_endpoint(self, mock_weekly, client):
        mock_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5, freq='W'),
            'close': [100 + i for i in range(5)],
            'volume': [1000 + i * 100 for i in range(5)]
        })
        mock_weekly.return_value = mock_data
        
        response = client.get("/api/alpha-vantage/weekly/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    @patch('api_server.stock_api.collector.get_alpha_vantage_weekly_data')
    def test_alpha_vantage_weekly_not_found(self, mock_weekly, client):
        mock_weekly.return_value = pd.DataFrame()
        
        response = client.get("/api/alpha-vantage/weekly/INVALID")
        assert response.status_code == 404
    
    @patch('api_server.stock_api.collector.get_alpha_vantage_monthly_data')
    def test_alpha_vantage_monthly_endpoint(self, mock_monthly, client):
        mock_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=3, freq='M'),
            'close': [100 + i for i in range(3)],
            'volume': [1000 + i * 100 for i in range(3)]
        })
        mock_monthly.return_value = mock_data
        
        response = client.get("/api/alpha-vantage/monthly/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    @patch('api_server.stock_api.collector.get_alpha_vantage_monthly_data')
    def test_alpha_vantage_monthly_not_found(self, mock_monthly, client):
        mock_monthly.return_value = pd.DataFrame()
        
        response = client.get("/api/alpha-vantage/monthly/INVALID")
        assert response.status_code == 404
    
    @patch('api_server.stock_api.notification_service.send_email')
    def test_send_email_notification_success(self, mock_send_email, client):
        mock_send_email.return_value = True
        
        response = client.post(
            "/api/notifications/email",
            params={
                "to_email": "test@example.com",
                "subject": "Test Subject",
                "body": "Test Body"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
    
    @patch('api_server.stock_api.notification_service.send_email')
    def test_send_email_notification_failure(self, mock_send_email, client):
        mock_send_email.return_value = False
        
        response = client.post(
            "/api/notifications/email",
            params={
                "to_email": "test@example.com",
                "subject": "Test Subject",
                "body": "Test Body"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
    
    @patch('api_server.stock_api.notification_service.send_email')
    def test_send_email_notification_exception(self, mock_send_email, client):
        mock_send_email.side_effect = Exception("Email error")
        
        response = client.post(
            "/api/notifications/email",
            params={
                "to_email": "test@example.com",
                "subject": "Test Subject",
                "body": "Test Body"
            }
        )
        
        assert response.status_code == 500
