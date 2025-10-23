import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
import asyncio
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app, StockAnalysisAPI
from fastapi.testclient import TestClient
from data_collectors.stock_data_collector import StockDataCollector
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService, AlertManager

class TestEndToEndWorkflows:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def stock_api(self):
        return StockAnalysisAPI()
    
    def test_complete_stock_analysis_workflow(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            with patch('api_server.stock_api._load_historical_data') as mock_historical:
                with patch('api_server.stock_api.analyzer.calculate_all_indicators') as mock_indicators:
                    with patch('api_server.stock_api.analyzer.analyze_trend') as mock_trend:
                        with patch('api_server.stock_api.analyzer.detect_anomalies') as mock_anomalies:
                            with patch('api_server.stock_api.analyzer.generate_signals') as mock_signals:
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
                                
                                mock_indicators.return_value = pd.DataFrame({
                                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                                    'close': 100 + np.cumsum(np.random.randn(30) * 0.5),
                                    'volume': np.random.randint(1000000, 5000000, 30),
                                    'rsi_14': np.random.uniform(20, 80, 30),
                                    'macd': np.random.randn(30) * 0.5,
                                    'bb_upper': 105 + np.random.randn(30) * 2,
                                    'bb_lower': 95 + np.random.randn(30) * 2
                                })
                                
                                mock_trend.return_value = {
                                    'trend': 'bullish',
                                    'strength': 0.8,
                                    'signals': ['RSI 과매도 - 매수 신호']
                                }
                                
                                mock_anomalies.return_value = [
                                    {
                                        'type': 'volume_spike',
                                        'severity': 'high',
                                        'message': 'AAPL: 거래량 급증'
                                    }
                                ]
                                
                                mock_signals.return_value = {
                                    'signal': 'buy',
                                    'confidence': 0.75,
                                    'signals': ['RSI 과매도 - 매수 신호'],
                                    'reason': '1개 매수 신호, 0개 매도 신호'
                                }
                                
                                response = client.get("/api/analysis/AAPL")
                                
                                assert response.status_code == 200
                                data = response.json()
                                assert data['symbol'] == 'AAPL'
                                assert data['current_price'] == 150.25
                                assert data['trend'] == 'bullish'
                                assert data['trend_strength'] == 0.8
                                assert data['signals']['signal'] == 'buy'
                                assert data['signals']['confidence'] == 0.75
                                assert len(data['anomalies']) == 1
                                assert data['anomalies'][0]['type'] == 'volume_spike'
    
    def test_complete_historical_data_workflow(self, client):
        with patch('api_server.stock_api._load_historical_data') as mock_historical:
            with patch('api_server.stock_api.analyzer.calculate_all_indicators') as mock_indicators:
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': 100 + np.cumsum(np.random.randn(30) * 0.5),
                    'volume': np.random.randint(1000000, 5000000, 30)
                })
                
                mock_indicators.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': 100 + np.cumsum(np.random.randn(30) * 0.5),
                    'volume': np.random.randint(1000000, 5000000, 30),
                    'rsi_14': np.random.uniform(20, 80, 30),
                    'macd': np.random.randn(30) * 0.5,
                    'bb_upper': 105 + np.random.randn(30) * 2,
                    'bb_lower': 95 + np.random.randn(30) * 2,
                    'sma_20': 100 + np.random.randn(30) * 1
                })
                
                response = client.get("/api/historical/AAPL?days=30")
                
                assert response.status_code == 200
                data = response.json()
                assert data['symbol'] == 'AAPL'
                assert data['period'] == 30
                assert len(data['data']) == 30
                assert all('rsi' in item for item in data['data'])
                assert all('macd' in item for item in data['data'])
                assert all('bb_upper' in item for item in data['data'])
                assert all('sma_20' in item for item in data['data'])
    
    def test_complete_notification_workflow(self, client):
        with patch('api_server.stock_api.notification_service.send_email') as mock_send_email:
            mock_send_email.return_value = True
            
            response = client.post(
                "/api/notifications/email",
                params={
                    "to_email": "analyst@company.com",
                    "subject": "주식 분석 리포트 - AAPL",
                    "body": "AAPL 종목 분석 결과: 상승 추세, 매수 신호"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert '이메일이 성공적으로 발송되었습니다' in data['message']
    
    def test_complete_websocket_workflow(self, client):
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
                    'anomalies': [
                        {
                            'type': 'price_spike',
                            'severity': 'medium',
                            'message': 'GOOGL: 가격 급등'
                        }
                    ],
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            with client.websocket_connect("/ws/realtime") as websocket:
                data = websocket.receive_text()
                parsed_data = json.loads(data)
                
                assert len(parsed_data) == 2
                assert parsed_data[0]['symbol'] == 'AAPL'
                assert parsed_data[0]['trend'] == 'bullish'
                assert parsed_data[1]['symbol'] == 'GOOGL'
                assert parsed_data[1]['trend'] == 'bearish'
                assert len(parsed_data[1]['anomalies']) == 1
    
    def test_complete_error_handling_workflow(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("API 연결 실패")
            
            response = client.get("/api/realtime/INVALID")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
            assert 'API 연결 실패' in data['detail']
    
    def test_complete_alpha_vantage_workflow(self, client):
        with patch('api_server.stock_api.collector.search_alpha_vantage_symbols') as mock_search:
            with patch('api_server.stock_api.collector.get_alpha_vantage_intraday_data') as mock_intraday:
                with patch('api_server.stock_api.collector.get_alpha_vantage_weekly_data') as mock_weekly:
                    with patch('api_server.stock_api.collector.get_alpha_vantage_monthly_data') as mock_monthly:
                        mock_search.return_value = [
                            {'symbol': 'AAPL', 'name': 'Apple Inc.'},
                            {'symbol': 'AAPL.US', 'name': 'Apple Inc. US'}
                        ]
                        
                        mock_intraday.return_value = pd.DataFrame({
                            'date': pd.date_range(start='2024-01-01', periods=10, freq='5min'),
                            'close': [150 + i for i in range(10)],
                            'volume': [1000 + i * 100 for i in range(10)]
                        })
                        
                        mock_weekly.return_value = pd.DataFrame({
                            'date': pd.date_range(start='2024-01-01', periods=5, freq='W'),
                            'close': [150 + i for i in range(5)],
                            'volume': [1000 + i * 100 for i in range(5)]
                        })
                        
                        mock_monthly.return_value = pd.DataFrame({
                            'date': pd.date_range(start='2024-01-01', periods=3, freq='M'),
                            'close': [150 + i for i in range(3)],
                            'volume': [1000 + i * 100 for i in range(3)]
                        })
                        
                        search_response = client.get("/api/alpha-vantage/search/Apple")
                        assert search_response.status_code == 200
                        search_data = search_response.json()
                        assert len(search_data) == 2
                        assert search_data[0]['symbol'] == 'AAPL'
                        
                        intraday_response = client.get("/api/alpha-vantage/intraday/AAPL")
                        assert intraday_response.status_code == 200
                        intraday_data = intraday_response.json()
                        assert len(intraday_data) == 10
                        
                        weekly_response = client.get("/api/alpha-vantage/weekly/AAPL")
                        assert weekly_response.status_code == 200
                        weekly_data = weekly_response.json()
                        assert len(weekly_data) == 5
                        
                        monthly_response = client.get("/api/alpha-vantage/monthly/AAPL")
                        assert monthly_response.status_code == 200
                        monthly_data = monthly_response.json()
                        assert len(monthly_data) == 3

class TestUserJourneyScenarios:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_analyst_daily_workflow(self, client):
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
                    'anomalies': [
                        {
                            'type': 'volume_spike',
                            'severity': 'high',
                            'message': 'GOOGL: 거래량 급증'
                        }
                    ],
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            response = client.get("/api/analysis/all")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            
            bullish_stocks = [stock for stock in data if stock['trend'] == 'bullish']
            bearish_stocks = [stock for stock in data if stock['trend'] == 'bearish']
            
            assert len(bullish_stocks) == 1
            assert len(bearish_stocks) == 1
            assert bullish_stocks[0]['symbol'] == 'AAPL'
            assert bearish_stocks[0]['symbol'] == 'GOOGL'
            
            high_anomaly_stocks = [stock for stock in data if any(
                anomaly['severity'] == 'high' for anomaly in stock['anomalies']
            )]
            assert len(high_anomaly_stocks) == 1
            assert high_anomaly_stocks[0]['symbol'] == 'GOOGL'
    
    def test_trader_realtime_monitoring_workflow(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            with patch('api_server.stock_api.get_analysis') as mock_analysis:
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
                
                realtime_response = client.get("/api/realtime/AAPL")
                assert realtime_response.status_code == 200
                realtime_data = realtime_response.json()
                assert realtime_data['symbol'] == 'AAPL'
                assert realtime_data['price'] == 150.25
                
                analysis_response = client.get("/api/analysis/AAPL")
                assert analysis_response.status_code == 200
                analysis_data = analysis_response.json()
                assert analysis_data['symbol'] == 'AAPL'
                assert analysis_data['trend'] == 'bullish'
                assert analysis_data['signals']['signal'] == 'buy'
    
    def test_portfolio_manager_historical_analysis_workflow(self, client):
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
                    },
                    {
                        'date': '2024-01-03',
                        'close': 152.0,
                        'volume': 1200000,
                        'rsi': 54.0,
                        'macd': 0.7,
                        'bb_upper': 157.0,
                        'bb_lower': 147.0,
                        'sma_20': 150.0
                    }
                ],
                'period': 30
            }
            
            response = client.get("/api/historical/AAPL?days=30")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert data['period'] == 30
            assert len(data['data']) == 3
            
            for item in data['data']:
                assert 'date' in item
                assert 'close' in item
                assert 'volume' in item
                assert 'rsi' in item
                assert 'macd' in item
                assert 'bb_upper' in item
                assert 'bb_lower' in item
                assert 'sma_20' in item
            
            prices = [item['close'] for item in data['data']]
            assert prices == [150.0, 151.0, 152.0]
            
            volumes = [item['volume'] for item in data['data']]
            assert volumes == [1000000, 1100000, 1200000]
    
    def test_risk_manager_anomaly_detection_workflow(self, client):
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
                        'message': 'AAPL: 거래량 급증 (5,000,000 vs 평균 2,000,000)',
                        'current_value': 5000000,
                        'threshold': 4000000
                    },
                    {
                        'type': 'price_spike',
                        'severity': 'medium',
                        'message': 'AAPL: 가격 급등 (10% 상승)',
                        'current_value': 150.25,
                        'threshold': 140.0
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            response = client.get("/api/analysis/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert len(data['anomalies']) == 2
            
            high_severity_anomalies = [a for a in data['anomalies'] if a['severity'] == 'high']
            medium_severity_anomalies = [a for a in data['anomalies'] if a['severity'] == 'medium']
            
            assert len(high_severity_anomalies) == 1
            assert len(medium_severity_anomalies) == 1
            assert high_severity_anomalies[0]['type'] == 'volume_spike'
            assert medium_severity_anomalies[0]['type'] == 'price_spike'
    
    def test_alert_manager_notification_workflow(self, client):
        with patch('api_server.stock_api.notification_service.send_email') as mock_send_email:
            with patch('api_server.stock_api.notification_service.send_slack_message') as mock_send_slack:
                mock_send_email.return_value = True
                mock_send_slack.return_value = True
                
                response = client.post(
                    "/api/notifications/email",
                    params={
                        "to_email": "risk@company.com",
                        "subject": "위험 알림 - AAPL 이상 패턴 감지",
                        "body": "AAPL에서 거래량 급증이 감지되었습니다. 즉시 확인이 필요합니다."
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['success'] is True
                assert '이메일이 성공적으로 발송되었습니다' in data['message']

class TestSystemResilience:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_concurrent_requests_handling(self, client):
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
            
            responses = []
            for i in range(10):
                response = client.get("/api/analysis/AAPL")
                responses.append(response)
            
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data['symbol'] == 'AAPL'
    
    def test_error_recovery_workflow(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = [
                Exception("첫 번째 시도 실패"),
                Exception("두 번째 시도 실패"),
                {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
            ]
            
            response = client.get("/api/realtime/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert data['price'] == 150.25
    
    def test_partial_failure_handling(self, client):
        with patch('api_server.stock_api.get_analysis') as mock_analysis:
            mock_analysis.side_effect = [
                {
                    'symbol': 'AAPL',
                    'current_price': 150.25,
                    'trend': 'bullish',
                    'trend_strength': 0.8,
                    'signals': {'signal': 'buy', 'confidence': 0.75},
                    'anomalies': [],
                    'timestamp': datetime.now().isoformat()
                },
                Exception("GOOGL 분석 실패"),
                {
                    'symbol': 'MSFT',
                    'current_price': 300.0,
                    'trend': 'bearish',
                    'trend_strength': 0.6,
                    'signals': {'signal': 'sell', 'confidence': 0.65},
                    'anomalies': [],
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            response = client.get("/api/analysis/all")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]['symbol'] == 'AAPL'
            assert data[1]['symbol'] == 'MSFT'
    
    def test_websocket_connection_stability(self, client):
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
                for i in range(5):
                    data = websocket.receive_text()
                    parsed_data = json.loads(data)
                    assert len(parsed_data) == 1
                    assert parsed_data[0]['symbol'] == 'AAPL'
    
    def test_data_validation_workflow(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.return_value = {
                'symbol': 'AAPL',
                'price': -150.25,
                'volume': -1000000,
                'change_percent': 0
            }
            
            response = client.get("/api/realtime/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert data['price'] == -150.25
            assert data['volume'] == -1000000
