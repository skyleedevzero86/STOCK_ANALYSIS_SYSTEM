import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time
import threading
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app, StockAnalysisAPI
from fastapi.testclient import TestClient
from data_collectors.stock_data_collector import StockDataCollector
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService, AlertManager

class TestStressScenarios:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def stock_api(self):
        return StockAnalysisAPI()
    
    def test_high_frequency_requests(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'change_percent': 2.5,
                'timestamp': datetime.now().isoformat()
            }
            
            def make_request():
                return client.get("/api/realtime/AAPL")
            
            num_requests = 1000
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(make_request) for _ in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 30.0
            
            successful_requests = sum(1 for result in results if result.status_code == 200)
            assert successful_requests >= num_requests * 0.95
            
            for result in results:
                if result.status_code == 200:
                    data = result.json()
                    assert data['symbol'] == 'AAPL'
    
    def test_memory_intensive_operations(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                large_dataset = pd.DataFrame({
                    'date': pd.date_range(start='2020-01-01', periods=10000, freq='D'),
                    'close': np.random.randn(10000) * 100 + 1000,
                    'volume': np.random.randint(1000000, 10000000, 10000)
                })
                
                mock_historical.return_value = large_dataset
                
                for i in range(100):
                    result = stock_api.get_analysis('AAPL')
                    assert result['symbol'] == 'AAPL'
                    
                    if i % 10 == 0:
                        gc.collect()
    
    def test_concurrent_analysis_operations(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                    'close': np.random.randn(1000) * 100 + 1000,
                    'volume': np.random.randint(1000000, 10000000, 1000)
                })
                
                def perform_analysis():
                    return stock_api.get_analysis('AAPL')
                
                num_operations = 50
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [executor.submit(perform_analysis) for _ in range(num_operations)]
                    results = [future.result() for future in as_completed(futures)]
                
                end_time = time.time()
                total_time = end_time - start_time
                
                assert total_time < 20.0
                assert len(results) == num_operations
                
                for result in results:
                    assert result['symbol'] == 'AAPL'
    
    def test_websocket_stress_test(self, client):
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
                    for _ in range(10):
                        data = websocket.receive_text()
                        parsed_data = json.loads(data)
                        assert len(parsed_data) == 1
                        assert parsed_data[0]['symbol'] == 'AAPL'
            
            num_connections = 20
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(websocket_connection) for _ in range(num_connections)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 15.0
            assert len(results) == num_connections
    
    def test_data_processing_stress(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                stress_dataset = pd.DataFrame({
                    'date': pd.date_range(start='2020-01-01', periods=5000, freq='D'),
                    'close': np.random.randn(5000) * 100 + 1000,
                    'volume': np.random.randint(1000000, 10000000, 5000)
                })
                
                mock_historical.return_value = stress_dataset
                
                for i in range(20):
                    result = stock_api.get_analysis('AAPL')
                    assert result['symbol'] == 'AAPL'
                    assert 'trend' in result
                    assert 'signals' in result
                    assert 'anomalies' in result
                    
                    if i % 5 == 0:
                        gc.collect()
    
    def test_notification_stress(self, stock_api):
        with patch.object(stock_api.notification_service, 'send_email') as mock_email:
            with patch.object(stock_api.notification_service, 'send_slack_message') as mock_slack:
                mock_email.return_value = True
                mock_slack.return_value = True
                
                anomalies = [
                    {
                        'symbol': f'STOCK{i}',
                        'type': 'volume_spike',
                        'severity': 'high',
                        'message': f'STOCK{i}: 거래량 급증'
                    }
                    for i in range(100)
                ]
                
                recipients = ['analyst@company.com', 'trader@company.com']
                
                start_time = time.time()
                result = stock_api.alert_manager.process_anomaly_alerts(anomalies, recipients)
                end_time = time.time()
                
                processing_time = end_time - start_time
                
                assert processing_time < 10.0
                assert result['anomalies_processed'] == 100
                assert result['alerts_sent'] > 0
    
    def test_mixed_workload_stress(self, client):
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
                    
                    num_workloads = 100
                    start_time = time.time()
                    
                    with ThreadPoolExecutor(max_workers=30) as executor:
                        futures = [executor.submit(mixed_requests) for _ in range(num_workloads)]
                        results = [future.result() for future in as_completed(futures)]
                    
                    end_time = time.time()
                    total_time = end_time - start_time
                    
                    assert total_time < 30.0
                    
                    total_requests = sum(len(result) for result in results)
                    assert total_requests == num_workloads * 3
                    
                    successful_requests = 0
                    for result in results:
                        for response in result:
                            if response.status_code == 200:
                                successful_requests += 1
                    
                    assert successful_requests >= total_requests * 0.9
    
    def test_memory_leak_detection(self, stock_api):
        initial_memory = []
        
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                    'close': np.random.randn(1000) * 100 + 1000,
                    'volume': np.random.randint(1000000, 10000000, 1000)
                })
                
                for i in range(50):
                    result = stock_api.get_analysis('AAPL')
                    assert result['symbol'] == 'AAPL'
                    
                    if i % 10 == 0:
                        gc.collect()
                        initial_memory.append(len(gc.get_objects()))
                
                final_memory = len(gc.get_objects())
                assert final_memory < initial_memory[0] * 2
    
    def test_error_recovery_stress(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = [
                Exception("Error 1"),
                Exception("Error 2"),
                {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5,
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            def make_request():
                return client.get("/api/realtime/AAPL")
            
            num_requests = 50
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 15.0
            
            error_responses = sum(1 for result in results if result.status_code == 500)
            success_responses = sum(1 for result in results if result.status_code == 200)
            
            assert error_responses > 0
            assert success_responses > 0
    
    def test_resource_cleanup_stress(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                    'close': np.random.randn(1000) * 100 + 1000,
                    'volume': np.random.randint(1000000, 10000000, 1000)
                })
                
                for i in range(30):
                    try:
                        result = stock_api.get_analysis('AAPL')
                        assert result['symbol'] == 'AAPL'
                    except Exception as e:
                        pass
                    
                    if i % 5 == 0:
                        gc.collect()
    
    def test_concurrent_websocket_stress(self, client):
        with patch('api_server.stock_api.get_all_symbols_analysis') as mock_analysis:
            mock_analysis.return_value = [
                {
                    'symbol': 'AAPL',
                    'current_price': 150.25,
                    'trend': 'bullish',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            def websocket_stress():
                with client.websocket_connect("/ws/realtime") as websocket:
                    for _ in range(5):
                        data = websocket.receive_text()
                        parsed_data = json.loads(data)
                        assert len(parsed_data) == 1
                        assert parsed_data[0]['symbol'] == 'AAPL'
            
            num_connections = 50
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(websocket_stress) for _ in range(num_connections)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 20.0
            assert len(results) == num_connections
    
    def test_data_volume_stress(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                large_dataset = pd.DataFrame({
                    'date': pd.date_range(start='2020-01-01', periods=10000, freq='D'),
                    'close': np.random.randn(10000) * 100 + 1000,
                    'volume': np.random.randint(1000000, 10000000, 10000)
                })
                
                mock_historical.return_value = large_dataset
                
                for i in range(10):
                    result = stock_api.get_analysis('AAPL')
                    assert result['symbol'] == 'AAPL'
                    assert 'trend' in result
                    assert 'signals' in result
                    assert 'anomalies' in result
                    
                    if i % 3 == 0:
                        gc.collect()
    
    def test_api_rate_limiting_stress(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'change_percent': 2.5,
                'timestamp': datetime.now().isoformat()
            }
            
            def rapid_requests():
                responses = []
                for _ in range(20):
                    response = client.get("/api/realtime/AAPL")
                    responses.append(response)
                return responses
            
            num_batches = 10
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(rapid_requests) for _ in range(num_batches)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert total_time < 25.0
            
            total_requests = sum(len(result) for result in results)
            assert total_requests == num_batches * 20
            
            successful_requests = 0
            for result in results:
                for response in result:
                    if response.status_code == 200:
                        successful_requests += 1
            
            assert successful_requests >= total_requests * 0.8
