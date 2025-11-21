import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time
import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app, StockAnalysisAPI
from fastapi.testclient import TestClient
from data_collectors.stock_data_collector import StockDataCollector
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService, AlertManager

class TestAPIPerformance:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_single_request_response_time(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'change_percent': 2.5,
                'timestamp': datetime.now().isoformat()
            }
            
            start_time = time.time()
            response = client.get("/api/realtime/AAPL")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0
            
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert data['price'] == 150.25
    
    def test_concurrent_requests_performance(self, client):
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
            
            def make_request():
                start_time = time.time()
                response = client.get("/api/analysis/AAPL")
                end_time = time.time()
                return response, end_time - start_time
            
            num_requests = 10
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 5.0
            
            for response, response_time in results:
                assert response.status_code == 200
                assert response_time < 1.0
                data = response.json()
                assert data['symbol'] == 'AAPL'
    
    def test_bulk_analysis_performance(self, client):
        with patch('api_server.stock_api.get_all_symbols_analysis') as mock_analysis:
            mock_analysis.return_value = [
                {
                    'symbol': 'AAPL',
                    'current_price': 150.25,
                    'trend': 'bullish',
                    'trend_strength': 0.8,
                    'signals': {'signal': 'buy', 'confidence': 0.75},
                    'anomalies': [],
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'symbol': 'GOOGL',
                    'current_price': 2500.0,
                    'trend': 'bearish',
                    'trend_strength': 0.6,
                    'signals': {'signal': 'sell', 'confidence': 0.65},
                    'anomalies': [],
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'symbol': 'MSFT',
                    'current_price': 300.0,
                    'trend': 'neutral',
                    'trend_strength': 0.5,
                    'signals': {'signal': 'hold', 'confidence': 0.5},
                    'anomalies': [],
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            start_time = time.time()
            response = client.get("/api/analysis/all")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0
            
            data = response.json()
            assert len(data) == 3
            assert all(stock['symbol'] in ['AAPL', 'GOOGL', 'MSFT'] for stock in data)
    
    def test_historical_data_performance(self, client):
        with patch('api_server.stock_api.get_historical_data') as mock_historical:
            mock_historical.return_value = {
                'symbol': 'AAPL',
                'data': [
                    {
                        'date': f'2024-01-{i:02d}',
                        'close': 150.0 + i,
                        'volume': 1000000 + i * 1000,
                        'rsi': 50.0 + i,
                        'macd': 0.5 + i * 0.1,
                        'bb_upper': 155.0 + i,
                        'bb_lower': 145.0 + i,
                        'sma_20': 148.0 + i
                    }
                    for i in range(1, 31)
                ],
                'period': 30
            }
            
            start_time = time.time()
            response = client.get("/api/historical/AAPL?days=30")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.5
            
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert len(data['data']) == 30
    
    def test_websocket_performance(self, client):
        with patch('api_server.stock_api.get_all_symbols_analysis') as mock_analysis:
            mock_analysis.return_value = [
                {
                    'symbol': 'AAPL',
                    'current_price': 150.25,
                    'trend': 'bullish',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            start_time = time.time()
            
            with client.websocket_connect("/ws/realtime") as websocket:
                data = websocket.receive_text()
                end_time = time.time()
                
                response_time = end_time - start_time
                
                assert response_time < 2.0
                
                parsed_data = json.loads(data)
                assert len(parsed_data) == 1
                assert parsed_data[0]['symbol'] == 'AAPL'
    
    def test_memory_usage_under_load(self, client):
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
            
            def make_requests():
                responses = []
                for _ in range(50):
                    response = client.get("/api/analysis/AAPL")
                    responses.append(response)
                return responses
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_requests) for _ in range(5)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 10.0
            
            total_requests = sum(len(result) for result in results)
            assert total_requests == 250
            
            for result in results:
                for response in result:
                    assert response.status_code == 200

class TestDataProcessingPerformance:
    
    @pytest.fixture
    def analyzer(self):
        return TechnicalAnalyzer()
    
    @pytest.fixture
    def large_dataset(self):
        dates = pd.date_range(start='2020-01-01', periods=1000, freq='D')
        np.random.seed(42)
        
        return pd.DataFrame({
            'date': dates,
            'close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })
    
    def test_rsi_calculation_performance(self, analyzer, large_dataset):
        start_time = time.time()
        rsi = analyzer.calculate_rsi(large_dataset)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        assert calculation_time < 1.0
        assert not rsi.empty
        assert len(rsi) == len(large_dataset)
        assert all(0 <= val <= 100 for val in rsi.dropna())
    
    def test_macd_calculation_performance(self, analyzer, large_dataset):
        start_time = time.time()
        macd_data = analyzer.calculate_macd(large_dataset)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        assert calculation_time < 1.0
        assert 'macd' in macd_data
        assert 'macd_signal' in macd_data
        assert 'macd_histogram' in macd_data
        assert not macd_data['macd'].empty
    
    def test_bollinger_bands_calculation_performance(self, analyzer, large_dataset):
        start_time = time.time()
        bb_data = analyzer.calculate_bollinger_bands(large_dataset)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        assert calculation_time < 1.0
        assert 'bb_upper' in bb_data
        assert 'bb_middle' in bb_data
        assert 'bb_lower' in bb_data
        assert not bb_data['bb_upper'].empty
    
    def test_moving_averages_calculation_performance(self, analyzer, large_dataset):
        start_time = time.time()
        ma_data = analyzer.calculate_moving_averages(large_dataset)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        assert calculation_time < 1.0
        assert 'sma_20' in ma_data
        assert 'sma_50' in ma_data
        assert 'ema_12' in ma_data
        assert 'ema_26' in ma_data
        assert not ma_data['sma_20'].empty
    
    def test_all_indicators_calculation_performance(self, analyzer, large_dataset):
        start_time = time.time()
        analyzed_data = analyzer.calculate_all_indicators(large_dataset)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        assert calculation_time < 2.0
        expected_columns = ['rsi_14', 'macd', 'macd_signal', 'macd_histogram', 
                           'bb_upper', 'bb_middle', 'bb_lower', 'sma_20', 'sma_50']
        
        for col in expected_columns:
            assert col in analyzed_data.columns
            assert not analyzed_data[col].empty
    
    def test_trend_analysis_performance(self, analyzer, large_dataset):
        analyzed_data = analyzer.calculate_all_indicators(large_dataset)
        
        start_time = time.time()
        trend_analysis = analyzer.analyze_trend(analyzed_data)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        assert calculation_time < 0.5
        assert 'trend' in trend_analysis
        assert 'strength' in trend_analysis
        assert 'signals' in trend_analysis
        assert trend_analysis['trend'] in ['bullish', 'bearish', 'neutral']
    
    def test_anomaly_detection_performance(self, analyzer, large_dataset):
        analyzed_data = analyzer.calculate_all_indicators(large_dataset)
        
        start_time = time.time()
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        assert calculation_time < 1.0
        assert isinstance(anomalies, list)
        for anomaly in anomalies:
            assert 'type' in anomaly
            assert 'severity' in anomaly
            assert 'message' in anomaly
    
    def test_signal_generation_performance(self, analyzer, large_dataset):
        analyzed_data = analyzer.calculate_all_indicators(large_dataset)
        
        start_time = time.time()
        signals = analyzer.generate_signals(analyzed_data, 'TEST')
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        assert calculation_time < 0.5
        assert 'signal' in signals
        assert 'confidence' in signals
        assert 'signals' in signals
        assert 'reason' in signals
        assert signals['signal'] in ['buy', 'sell', 'hold']

class TestDataCollectionPerformance:
    
    @pytest.fixture
    def collector(self):
        return StockDataCollector(['AAPL', 'GOOGL', 'MSFT'], use_mock_data=True)
    
    def test_historical_data_collection_performance(self, collector):
        start_time = time.time()
        data = collector.get_historical_data('AAPL', period='1mo')
        end_time = time.time()
        
        collection_time = end_time - start_time
        
        assert collection_time < 2.0
        if not data.empty:
            assert 'close' in data.columns
            assert 'volume' in data.columns
            assert 'symbol' in data.columns
    
    def test_realtime_data_collection_performance(self, collector):
        start_time = time.time()
        data = collector.get_realtime_data('AAPL')
        end_time = time.time()
        
        collection_time = end_time - start_time
        
        assert collection_time < 1.0
        if data:
            assert 'symbol' in data
            assert 'price' in data
            assert 'timestamp' in data
    
    def test_batch_data_collection_performance(self, collector):
        start_time = time.time()
        all_data = collector.collect_batch_data()
        end_time = time.time()
        
        collection_time = end_time - start_time
        
        assert collection_time < 3.0
        assert isinstance(all_data, dict)
        for symbol, data in all_data.items():
            assert symbol in collector.symbols
            assert isinstance(data, pd.DataFrame)
            assert not data.empty
    
    def test_multiple_realtime_data_performance(self, collector):
        start_time = time.time()
        results = collector.get_multiple_realtime_data()
        end_time = time.time()
        
        collection_time = end_time - start_time
        
        assert collection_time < 2.0
        assert isinstance(results, list)
        assert len(results) <= len(collector.symbols)
        
        for data in results:
            if data:
                assert 'symbol' in data
                assert 'price' in data
                assert 'timestamp' in data

class TestNotificationPerformance:
    
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
    
    def test_email_sending_performance(self, notification_service):
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            start_time = time.time()
            result = notification_service.send_email(
                to_email='test@example.com',
                subject='Test Subject',
                body='Test Body'
            )
            end_time = time.time()
            
            sending_time = end_time - start_time
            
            assert result is True
            assert sending_time < 1.0
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()
    
    def test_slack_message_performance(self, notification_service):
        with patch('requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            start_time = time.time()
            result = notification_service.send_slack_message("Test message")
            end_time = time.time()
            
            sending_time = end_time - start_time
            
            assert result is True
            assert sending_time < 0.5
            mock_post.assert_called_once()
    
    def test_bulk_notification_performance(self, notification_service):
        with patch.object(notification_service, 'send_email') as mock_email:
            with patch.object(notification_service, 'send_slack_message') as mock_slack:
                mock_email.return_value = True
                mock_slack.return_value = True
                
                notifications = [
                    {'type': 'email', 'recipient': f'test{i}@example.com', 'subject': 'Test', 'content': 'Test'}
                    for i in range(10)
                ] + [
                    {'type': 'slack', 'content': f'Test message {i}'}
                    for i in range(5)
                ]
                
                start_time = time.time()
                result = notification_service.send_bulk_notifications(notifications)
                end_time = time.time()
                
                processing_time = end_time - start_time
                
                assert result['email_success'] == 10
                assert result['slack_success'] == 5
                assert result['total_sent'] == 15
                assert processing_time < 2.0
    
    def test_alert_processing_performance(self, alert_manager):
        anomalies = [
            {
                'symbol': f'STOCK{i}',
                'type': 'volume_spike',
                'severity': 'high',
                'message': f'STOCK{i}: 거래량 급증'
            }
            for i in range(20)
        ]
        
        recipients = ['analyst@company.com', 'trader@company.com']
        
        start_time = time.time()
        result = alert_manager.process_anomaly_alerts(anomalies, recipients)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert result['alerts_sent'] > 0
        assert result['anomalies_processed'] == 20
        assert processing_time < 3.0

class TestSystemLoadPerformance:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_high_concurrency_performance(self, client):
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
            
            def make_request():
                return client.get("/api/analysis/AAPL")
            
            num_requests = 100
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(make_request) for _ in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 10.0
            
            successful_requests = sum(1 for result in results if result.status_code == 200)
            assert successful_requests == num_requests
            
            for result in results:
                assert result.status_code == 200
                data = result.json()
                assert data['symbol'] == 'AAPL'
    
    def test_memory_efficiency_under_load(self, client):
        with patch('api_server.stock_api.get_historical_data') as mock_historical:
            mock_historical.return_value = {
                'symbol': 'AAPL',
                'data': [
                    {
                        'date': f'2024-01-{i:02d}',
                        'close': 150.0 + i,
                        'volume': 1000000 + i * 1000,
                        'rsi': 50.0 + i,
                        'macd': 0.5 + i * 0.1,
                        'bb_upper': 155.0 + i,
                        'bb_lower': 145.0 + i,
                        'sma_20': 148.0 + i
                    }
                    for i in range(1, 31)
                ],
                'period': 30
            }
            
            def make_historical_request():
                return client.get("/api/historical/AAPL?days=30")
            
            num_requests = 50
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_historical_request) for _ in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 15.0
            
            successful_requests = sum(1 for result in results if result.status_code == 200)
            assert successful_requests == num_requests
            
            for result in results:
                assert result.status_code == 200
                data = result.json()
                assert data['symbol'] == 'AAPL'
                assert len(data['data']) == 30
    
    def test_websocket_concurrent_connections(self, client):
        with patch('api_server.stock_api.get_all_symbols_analysis') as mock_analysis:
            mock_analysis.return_value = [
                {
                    'symbol': 'AAPL',
                    'current_price': 150.25,
                    'trend': 'bullish',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            def websocket_connection():
                with client.websocket_connect("/ws/realtime") as websocket:
                    data = websocket.receive_text()
                    parsed_data = json.loads(data)
                    return parsed_data
            
            num_connections = 10
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(websocket_connection) for _ in range(num_connections)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 5.0
            
            for result in results:
                assert len(result) == 1
                assert result[0]['symbol'] == 'AAPL'
    
    def test_mixed_workload_performance(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            with patch('api_server.stock_api.get_analysis') as mock_analysis:
                with patch('api_server.stock_api.get_historical_data') as mock_historical:
                    mock_realtime.return_value = {
                        'symbol': 'AAPL',
                        'price': 150.25,
                        'volume': 1000000,
                        'change_percent': 2.5,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    mock_analysis.return_value = {
                        'symbol': 'AAPL',
                        'current_price': 150.25,
                        'trend': 'bullish',
                        'trend_strength': 0.8,
                        'signals': {'signal': 'buy', 'confidence': 0.75},
                        'anomalies': [],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    mock_historical.return_value = {
                        'symbol': 'AAPL',
                        'data': [
                            {
                                'date': f'2024-01-{i:02d}',
                                'close': 150.0 + i,
                                'volume': 1000000 + i * 1000,
                                'rsi': 50.0 + i,
                                'macd': 0.5 + i * 0.1,
                                'bb_upper': 155.0 + i,
                                'bb_lower': 145.0 + i,
                                'sma_20': 148.0 + i
                            }
                            for i in range(1, 31)
                        ],
                        'period': 30
                    }
                    
                    def mixed_requests():
                        results = []
                        results.append(client.get("/api/realtime/AAPL"))
                        results.append(client.get("/api/analysis/AAPL"))
                        results.append(client.get("/api/historical/AAPL?days=30"))
                        return results
                    
                    num_workloads = 20
                    start_time = time.time()
                    
                    with ThreadPoolExecutor(max_workers=15) as executor:
                        futures = [executor.submit(mixed_requests) for _ in range(num_workloads)]
                        results = [future.result() for future in as_completed(futures)]
                    
                    end_time = time.time()
                    total_time = end_time - start_time
                    
                    assert total_time < 20.0
                    
                    total_requests = sum(len(result) for result in results)
                    assert total_requests == num_workloads * 3
                    
                    for result in results:
                        for response in result:
                            assert response.status_code == 200
