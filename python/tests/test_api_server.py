import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app, StockAnalysisAPI

class TestAPIEndpoints:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_stock_api(self):
        with patch('api_server.stock_api') as mock:
            yield mock
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_get_symbols(self, client):
        response = client.get("/api/symbols")
        assert response.status_code == 200
        data = response.json()
        assert "symbols" in data
        assert isinstance(data["symbols"], list)
    
    @patch('api_server.stock_api.get_realtime_data')
    def test_get_realtime_data_success(self, mock_get_realtime, client):
        mock_data = {
            'symbol': 'AAPL',
            'price': 150.25,
            'volume': 1000000,
            'change_percent': 2.5,
            'timestamp': '2024-01-01T10:00:00'
        }
        mock_get_realtime.return_value = mock_data
        
        response = client.get("/api/realtime/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data['symbol'] == 'AAPL'
        assert data['price'] == 150.25
    
    @patch('api_server.stock_api.get_realtime_data')
    def test_get_realtime_data_not_found(self, mock_get_realtime, client):
        mock_get_realtime.side_effect = Exception("Data not found")
        
        response = client.get("/api/realtime/INVALID")
        assert response.status_code == 500
    
    @patch('api_server.stock_api.get_analysis')
    def test_get_analysis_success(self, mock_get_analysis, client):
        mock_analysis = {
            'symbol': 'AAPL',
            'current_price': 150.25,
            'trend': 'bullish',
            'trend_strength': 0.8,
            'signals': {'signal': 'buy', 'confidence': 0.75},
            'anomalies': [],
            'timestamp': '2024-01-01T10:00:00'
        }
        mock_get_analysis.return_value = mock_analysis
        
        response = client.get("/api/analysis/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data['symbol'] == 'AAPL'
        assert data['trend'] == 'bullish'
    
    @patch('api_server.stock_api.get_historical_data')
    def test_get_historical_data_success(self, mock_get_historical, client):
        mock_data = {
            'symbol': 'AAPL',
            'data': [
                {'date': '2024-01-01', 'close': 150.0, 'volume': 1000000},
                {'date': '2024-01-02', 'close': 151.0, 'volume': 1100000}
            ],
            'period': 30
        }
        mock_get_historical.return_value = mock_data
        
        response = client.get("/api/historical/AAPL?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data['symbol'] == 'AAPL'
        assert len(data['data']) == 2
    
    @patch('api_server.stock_api.get_historical_data')
    def test_get_historical_data_with_invalid_days(self, mock_get_historical, client):
        response = client.get("/api/historical/AAPL?days=500")
        assert response.status_code == 422
    
    @patch('api_server.stock_api.get_all_symbols_analysis')
    def test_get_all_analysis_success(self, mock_get_all, client):
        mock_analyses = [
            {
                'symbol': 'AAPL',
                'current_price': 150.25,
                'trend': 'bullish',
                'trend_strength': 0.8,
                'signals': {'signal': 'buy', 'confidence': 0.75},
                'anomalies': [],
                'timestamp': '2024-01-01T10:00:00'
            },
            {
                'symbol': 'GOOGL',
                'current_price': 2500.0,
                'trend': 'bearish',
                'trend_strength': 0.6,
                'signals': {'signal': 'sell', 'confidence': 0.65},
                'anomalies': [],
                'timestamp': '2024-01-01T10:00:00'
            }
        ]
        mock_get_all.return_value = mock_analyses
        
        response = client.get("/api/analysis/all")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['symbol'] == 'AAPL'
        assert data[1]['symbol'] == 'GOOGL'
    
    def test_websocket_endpoint(self, client):
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("ping")
            data = websocket.receive_text()
            assert data == "pong"
    
    @patch('api_server.stock_api.get_all_symbols_analysis')
    def test_websocket_realtime_endpoint(self, mock_get_all, client):
        mock_analyses = [
            {
                'symbol': 'AAPL',
                'current_price': 150.25,
                'trend': 'bullish',
                'timestamp': '2024-01-01T10:00:00'
            }
        ]
        mock_get_all.return_value = mock_analyses
        
        with client.websocket_connect("/ws/realtime") as websocket:
            data = websocket.receive_text()
            parsed_data = json.loads(data)
            assert len(parsed_data) == 1
            assert parsed_data[0]['symbol'] == 'AAPL'

class TestStockAnalysisAPI:
    
    @pytest.fixture
    def stock_api(self):
        return StockAnalysisAPI()
    
    @patch('api_server.StockDataCollector')
    @patch('api_server.TechnicalAnalyzer')
    @patch('api_server.NotificationService')
    @patch('api_server.AlertManager')
    def test_initialization(self, mock_alert_manager, mock_notification, mock_analyzer, mock_collector):
        api = StockAnalysisAPI()
        
        assert api.symbols is not None
        assert api.collector is not None
        assert api.analyzer is not None
        assert api.notification_service is not None
        assert api.alert_manager is not None
    
    @patch('api_server.StockDataCollector')
    def test_get_realtime_data_success(self, mock_collector_class, stock_api):
        mock_collector = Mock()
        mock_collector.get_realtime_data.return_value = {
            'symbol': 'AAPL',
            'price': 150.25,
            'volume': 1000000,
            'change_percent': 2.5
        }
        mock_collector_class.return_value = mock_collector
        stock_api.collector = mock_collector
        
        result = stock_api.get_realtime_data('AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['price'] == 150.25
        mock_collector.get_realtime_data.assert_called_once_with('AAPL')
    
    @patch('api_server.StockDataCollector')
    def test_get_realtime_data_failure(self, mock_collector_class, stock_api):
        mock_collector = Mock()
        mock_collector.get_realtime_data.return_value = {}
        mock_collector_class.return_value = mock_collector
        stock_api.collector = mock_collector
        
        with pytest.raises(Exception):
            stock_api.get_realtime_data('INVALID')
    
    @patch('api_server.StockDataCollector')
    @patch('api_server.TechnicalAnalyzer')
    def test_get_analysis_success(self, mock_analyzer_class, mock_collector_class, stock_api):
        mock_collector = Mock()
        mock_collector.get_realtime_data.return_value = {
            'symbol': 'AAPL',
            'price': 150.25,
            'volume': 1000000,
            'change_percent': 2.5
        }
        mock_collector_class.return_value = mock_collector
        stock_api.collector = mock_collector
        
        mock_analyzer = Mock()
        mock_analyzer.calculate_all_indicators.return_value = Mock()
        mock_analyzer.analyze_trend.return_value = {'trend': 'bullish', 'strength': 0.8}
        mock_analyzer.detect_anomalies.return_value = []
        mock_analyzer.generate_signals.return_value = {'signal': 'buy', 'confidence': 0.75}
        mock_analyzer_class.return_value = mock_analyzer
        stock_api.analyzer = mock_analyzer
        
        result = stock_api.get_analysis('AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['trend'] == 'bullish'
        assert result['signals']['signal'] == 'buy'
    
    @patch('api_server.StockDataCollector')
    @patch('api_server.TechnicalAnalyzer')
    def test_get_historical_data_success(self, mock_analyzer_class, mock_collector_class, stock_api):
        mock_analyzer = Mock()
        mock_analyzer.calculate_all_indicators.return_value = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        stock_api.analyzer = mock_analyzer
        
        result = stock_api.get_historical_data('AAPL', 30)
        
        assert result['symbol'] == 'AAPL'
        assert result['period'] == 30
        assert 'data' in result
    
    def test_get_all_symbols_analysis_success(self, stock_api):
        with patch.object(stock_api, 'get_analysis') as mock_get_analysis:
            mock_get_analysis.return_value = {
                'symbol': 'AAPL',
                'trend': 'bullish',
                'signals': {'signal': 'buy'}
            }
            
            result = stock_api.get_all_symbols_analysis()
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert result[0]['symbol'] == 'AAPL'
    
    def test_get_all_symbols_analysis_with_errors(self, stock_api):
        with patch.object(stock_api, 'get_analysis') as mock_get_analysis:
            mock_get_analysis.side_effect = [Exception("Error"), {
                'symbol': 'GOOGL',
                'trend': 'bearish',
                'signals': {'signal': 'sell'}
            }]
            
            result = stock_api.get_all_symbols_analysis()
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]['symbol'] == 'GOOGL'
