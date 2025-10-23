import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import asyncio
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app, StockAnalysisAPI
from fastapi.testclient import TestClient
from data_collectors.stock_data_collector import StockDataCollector
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService, AlertManager

class TestDataFlowIntegration:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def stock_api(self):
        return StockAnalysisAPI()
    
    def test_complete_data_collection_flow(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': 100 + np.cumsum(np.random.randn(30) * 0.5),
                    'volume': np.random.randint(1000000, 5000000, 30)
                })
                
                result = stock_api.get_analysis('AAPL')
                
                assert result['symbol'] == 'AAPL'
                assert result['current_price'] == 150.25
                assert 'trend' in result
                assert 'signals' in result
                assert 'anomalies' in result
    
    def test_complete_notification_flow(self, stock_api):
        with patch.object(stock_api.notification_service, 'send_email') as mock_email:
            with patch.object(stock_api.notification_service, 'send_slack_message') as mock_slack:
                mock_email.return_value = True
                mock_slack.return_value = True
                
                anomalies = [
                    {
                        'symbol': 'AAPL',
                        'type': 'volume_spike',
                        'severity': 'high',
                        'message': 'AAPL: 거래량 급증'
                    }
                ]
                
                recipients = ['analyst@company.com']
                
                result = stock_api.alert_manager.process_anomaly_alerts(anomalies, recipients)
                
                assert result['alerts_sent'] > 0
                assert result['anomalies_processed'] == 1
                mock_email.assert_called()
                mock_slack.assert_called()
    
    def test_api_to_analysis_integration(self, client):
        with patch('api_server.stock_api.get_analysis') as mock_analysis:
            mock_analysis.return_value = {
                'symbol': 'AAPL',
                'current_price': 150.25,
                'trend': 'bullish',
                'trend_strength': 0.8,
                'signals': {'signal': 'buy', 'confidence': 0.75},
                'anomalies': [],
                'timestamp': datetime.now().isoformat()
            }
            
            response = client.get("/api/analysis/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert data['trend'] == 'bullish'
            assert data['signals']['signal'] == 'buy'
    
    def test_websocket_integration(self, client):
        with patch('api_server.stock_api.get_all_symbols_analysis') as mock_analysis:
            mock_analysis.return_value = [
                {
                    'symbol': 'AAPL',
                    'current_price': 150.25,
                    'trend': 'bullish',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            with client.websocket_connect("/ws/realtime") as websocket:
                data = websocket.receive_text()
                parsed_data = json.loads(data)
                
                assert len(parsed_data) == 1
                assert parsed_data[0]['symbol'] == 'AAPL'
    
    def test_historical_data_integration(self, client):
        with patch('api_server.stock_api.get_historical_data') as mock_historical:
            mock_historical.return_value = {
                'symbol': 'AAPL',
                'data': [
                    {
                        'date': '2024-01-01',
                        'close': 150.0,
                        'volume': 1000000,
                        'rsi': 50.0,
                        'macd': 0.5,
                        'bb_upper': 155.0,
                        'bb_lower': 145.0,
                        'sma_20': 148.0
                    }
                ],
                'period': 30
            }
            
            response = client.get("/api/historical/AAPL?days=30")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert len(data['data']) == 1
            assert 'rsi' in data['data'][0]
            assert 'macd' in data['data'][0]
    
    def test_error_handling_integration(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("API Error")
            
            response = client.get("/api/realtime/INVALID")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
    
    def test_batch_processing_integration(self, stock_api):
        with patch.object(stock_api, 'get_analysis') as mock_analysis:
            mock_analysis.side_effect = [
                {'symbol': 'AAPL', 'trend': 'bullish'},
                {'symbol': 'GOOGL', 'trend': 'bearish'},
                Exception("Error for MSFT")
            ]
            
            result = stock_api.get_all_symbols_analysis()
            
            assert len(result) == 2
            assert result[0]['symbol'] == 'AAPL'
            assert result[1]['symbol'] == 'GOOGL'
    
    def test_data_quality_integration(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 0,
                    'volume': 0,
                    'change_percent': 0
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=5, freq='D'),
                    'close': [0, -10, 50, 0, 100],
                    'volume': [0, 1000, 0, 2000, 0]
                })
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')

class TestSystemIntegration:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_check_integration(self, client):
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_symbols_endpoint_integration(self, client):
        response = client.get("/api/symbols")
        
        assert response.status_code == 200
        data = response.json()
        assert 'symbols' in data
        assert isinstance(data['symbols'], list)
        assert len(data['symbols']) > 0
    
    def test_root_endpoint_integration(self, client):
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'version' in data
    
    def test_cors_integration(self, client):
        response = client.options("/api/health")
        
        assert response.status_code == 200
    
    def test_websocket_ping_pong_integration(self, client):
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("ping")
            data = websocket.receive_text()
            assert data == "pong"
    
    def test_websocket_disconnect_integration(self, client):
        with client.websocket_connect("/ws") as websocket:
            websocket.close()
    
    def test_multiple_websocket_connections(self, client):
        with client.websocket_connect("/ws") as websocket1:
            with client.websocket_connect("/ws") as websocket2:
                websocket1.send_text("ping")
                websocket2.send_text("ping")
                
                data1 = websocket1.receive_text()
                data2 = websocket2.receive_text()
                
                assert data1 == "pong"
                assert data2 == "pong"

class TestDataCollectorIntegration:
    
    @pytest.fixture
    def collector(self):
        return StockDataCollector(['AAPL', 'GOOGL'], use_mock_data=True)
    
    def test_collector_initialization_integration(self, collector):
        assert collector.symbols == ['AAPL', 'GOOGL']
        assert collector.session is not None
        assert collector.use_mock_data is True
    
    def test_historical_data_collection_integration(self, collector):
        data = collector.get_historical_data('AAPL', period='1mo')
        
        if not data.empty:
            assert 'close' in data.columns
            assert 'volume' in data.columns
            assert 'symbol' in data.columns
            assert data['symbol'].iloc[0] == 'AAPL'
    
    def test_realtime_data_collection_integration(self, collector):
        data = collector.get_realtime_data('AAPL')
        
        if data:
            assert 'symbol' in data
            assert 'price' in data
            assert 'timestamp' in data
            assert data['symbol'] == 'AAPL'
    
    def test_batch_data_collection_integration(self, collector):
        all_data = collector.collect_batch_data()
        
        assert isinstance(all_data, dict)
        for symbol, data in all_data.items():
            assert symbol in collector.symbols
            assert isinstance(data, pd.DataFrame)
            assert not data.empty

class TestAnalysisEngineIntegration:
    
    @pytest.fixture
    def analyzer(self):
        return TechnicalAnalyzer()
    
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        np.random.seed(42)
        
        return pd.DataFrame({
            'date': dates,
            'close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })
    
    def test_analysis_pipeline_integration(self, analyzer, sample_data):
        analyzed_data = analyzer.calculate_all_indicators(sample_data)
        
        assert 'rsi_14' in analyzed_data.columns
        assert 'macd' in analyzed_data.columns
        assert 'bb_upper' in analyzed_data.columns
        assert 'sma_20' in analyzed_data.columns
        
        trend_analysis = analyzer.analyze_trend(analyzed_data)
        assert 'trend' in trend_analysis
        assert 'strength' in trend_analysis
        
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        assert isinstance(anomalies, list)
        
        signals = analyzer.generate_signals(analyzed_data, 'TEST')
        assert 'signal' in signals
        assert 'confidence' in signals
    
    def test_analysis_with_extreme_data_integration(self, analyzer):
        extreme_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100] * 29 + [200],
            'volume': [1000] * 29 + [10000000]
        })
        
        analyzed_data = analyzer.calculate_all_indicators(extreme_data)
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        
        assert len(anomalies) > 0
        assert any(a['type'] in ['price_spike', 'volume_spike'] for a in anomalies)

class TestNotificationIntegration:
    
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
    
    @pytest.fixture
    def alert_manager(self, notification_service):
        return AlertManager(notification_service)
    
    def test_notification_service_integration(self, notification_service):
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            result = notification_service.send_email(
                to_email='test@example.com',
                subject='Test',
                body='Test'
            )
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()
    
    def test_alert_manager_integration(self, alert_manager):
        anomalies = [
            {
                'symbol': 'AAPL',
                'type': 'volume_spike',
                'severity': 'high',
                'message': 'AAPL: 거래량 급증'
            }
        ]
        
        recipients = ['analyst@company.com']
        
        result = alert_manager.process_anomaly_alerts(anomalies, recipients)
        
        assert result['alerts_sent'] > 0
        assert result['anomalies_processed'] == 1
        assert len(alert_manager.alert_history) == 1
    
    def test_bulk_notification_integration(self, notification_service):
        with patch.object(notification_service, 'send_email') as mock_email:
            with patch.object(notification_service, 'send_slack_message') as mock_slack:
                mock_email.return_value = True
                mock_slack.return_value = True
                
                notifications = [
                    {'type': 'email', 'recipient': 'test@example.com', 'subject': 'Test', 'content': 'Test'},
                    {'type': 'slack', 'content': 'Test message'}
                ]
                
                result = notification_service.send_bulk_notifications(notifications)
                
                assert result['email_success'] == 1
                assert result['slack_success'] == 1
                assert result['total_sent'] == 2

class TestEndToEndIntegration:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_analysis_workflow(self, client):
        with patch('api_server.stock_api.get_analysis') as mock_analysis:
            mock_analysis.return_value = {
                'symbol': 'AAPL',
                'current_price': 150.25,
                'trend': 'bullish',
                'trend_strength': 0.8,
                'signals': {'signal': 'buy', 'confidence': 0.75},
                'anomalies': [
                    {
                        'type': 'volume_spike',
                        'severity': 'high',
                        'message': 'AAPL: 거래량 급증'
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            response = client.get("/api/analysis/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert data['trend'] == 'bullish'
            assert data['signals']['signal'] == 'buy'
            assert len(data['anomalies']) == 1
            assert data['anomalies'][0]['type'] == 'volume_spike'
    
    def test_complete_historical_workflow(self, client):
        with patch('api_server.stock_api.get_historical_data') as mock_historical:
            mock_historical.return_value = {
                'symbol': 'AAPL',
                'data': [
                    {
                        'date': '2024-01-01',
                        'close': 150.0,
                        'volume': 1000000,
                        'rsi': 50.0,
                        'macd': 0.5,
                        'bb_upper': 155.0,
                        'bb_lower': 145.0,
                        'sma_20': 148.0
                    },
                    {
                        'date': '2024-01-02',
                        'close': 151.0,
                        'volume': 1100000,
                        'rsi': 52.0,
                        'macd': 0.6,
                        'bb_upper': 156.0,
                        'bb_lower': 146.0,
                        'sma_20': 149.0
                    }
                ],
                'period': 30
            }
            
            response = client.get("/api/historical/AAPL?days=30")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert len(data['data']) == 2
            assert all('rsi' in item for item in data['data'])
            assert all('macd' in item for item in data['data'])
    
    def test_complete_notification_workflow(self, client):
        with patch('api_server.stock_api.notification_service.send_email') as mock_send_email:
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
            assert '이메일이 성공적으로 발송되었습니다' in data['message']
    
    def test_error_handling_workflow(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("API Error")
            
            response = client.get("/api/realtime/INVALID")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
            assert 'API Error' in data['detail']
    
    def test_websocket_realtime_workflow(self, client):
        with patch('api_server.stock_api.get_all_symbols_analysis') as mock_analysis:
            mock_analysis.return_value = [
                {
                    'symbol': 'AAPL',
                    'current_price': 150.25,
                    'trend': 'bullish',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'symbol': 'GOOGL',
                    'current_price': 2500.0,
                    'trend': 'bearish',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            with client.websocket_connect("/ws/realtime") as websocket:
                data = websocket.receive_text()
                parsed_data = json.loads(data)
                
                assert len(parsed_data) == 2
                assert parsed_data[0]['symbol'] == 'AAPL'
                assert parsed_data[1]['symbol'] == 'GOOGL'
