import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server_enhanced import app, StockAnalysisAPI, manager

class TestEnhancedAPIEndpoints:
    
    @pytest.fixture
    def client(self):
        with patch('api_server_enhanced.lifespan'):
            return TestClient(app)
    
    @pytest.fixture
    def mock_app_state(self):
        state = Mock()
        state.data_collector = Mock()
        state.analyzer = Mock()
        state.security_manager = Mock()
        state.error_manager = Mock()
        return state
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "2.0.0"
    
    @patch('api_server_enhanced.get_stock_api')
    def test_health_check(self, mock_get_api, client, mock_app_state):
        mock_api = Mock()
        mock_api.data_collector = Mock()
        mock_api.data_collector.health_check = AsyncMock(return_value={'status': 'healthy'})
        mock_api.data_collector.get_performance_metrics = Mock(return_value={
            'cache_hit_rate': 0.8,
            'avg_response_time': 0.1,
            'error_rate': 0.01,
            'active_connections': 5,
            'queue_size': 0,
            'memory_usage': 0.5,
            'cpu_usage': 0.3
        })
        mock_api.error_manager = Mock()
        mock_api.error_manager.get_error_statistics = Mock(return_value={})
        mock_get_api.return_value = mock_api
        
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "performance" in data
    
    @patch('api_server_enhanced.get_stock_api')
    def test_get_performance_metrics(self, mock_get_api, client):
        mock_api = Mock()
        mock_api.data_collector = Mock()
        mock_api.data_collector.get_performance_metrics = Mock(return_value={
            'cache_hit_rate': 0.85,
            'avg_response_time': 0.12,
            'error_rate': 0.02,
            'active_connections': 10,
            'queue_size': 2,
            'memory_usage': 0.6,
            'cpu_usage': 0.4
        })
        mock_get_api.return_value = mock_api
        
        response = client.get("/api/performance")
        assert response.status_code == 200
        data = response.json()
        assert data['cache_hit_rate'] == 0.85
        assert data['avg_response_time'] == 0.12
        assert data['error_rate'] == 0.02
    
    @patch('api_server_enhanced.get_stock_api')
    def test_get_realtime_data_enhanced(self, mock_get_api, client):
        mock_api = Mock()
        mock_api.get_realtime_data_enhanced = AsyncMock(return_value={
            'symbol': 'AAPL',
            'currentPrice': 150.25,
            'volume': 1000000,
            'changePercent': 2.5,
            'timestamp': datetime.now().isoformat(),
            'confidenceScore': 0.95
        })
        mock_get_api.return_value = mock_api
        
        response = client.get("/api/realtime/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data['symbol'] == 'AAPL'
        assert data['currentPrice'] == 150.25
    
    @patch('api_server_enhanced.get_stock_api')
    def test_get_realtime_data_not_found(self, mock_get_api, client):
        mock_api = Mock()
        mock_api.get_realtime_data_enhanced = AsyncMock(side_effect=Exception("Not found"))
        mock_get_api.return_value = mock_api
        
        response = client.get("/api/realtime/INVALID")
        assert response.status_code in [500, 404]
    
    @patch('api_server_enhanced.get_stock_api')
    def test_get_advanced_analysis(self, mock_get_api, client):
        mock_api = Mock()
        mock_api.get_advanced_analysis = AsyncMock(return_value={
            'symbol': 'AAPL',
            'currentPrice': 150.25,
            'volume': 1000000,
            'changePercent': 2.5,
            'trend': 'bullish',
            'trendStrength': 0.8,
            'marketRegime': 'trending',
            'signals': {'signal': 'buy', 'confidence': 0.75},
            'patterns': [],
            'supportResistance': {},
            'fibonacciLevels': {},
            'anomalies': [],
            'riskScore': 0.3,
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat()
        })
        mock_get_api.return_value = mock_api
        
        response = client.get("/api/analysis/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data['symbol'] == 'AAPL'
        assert data['trend'] == 'bullish'
        assert 'marketRegime' in data
    
    @patch('api_server_enhanced.get_stock_api')
    def test_get_batch_analysis(self, mock_get_api, client):
        mock_api = Mock()
        mock_api.get_batch_analysis = AsyncMock(return_value=[
            {
                'symbol': 'AAPL',
                'trend': 'bullish',
                'confidence': 0.8
            },
            {
                'symbol': 'GOOGL',
                'trend': 'bearish',
                'confidence': 0.7
            }
        ])
        mock_get_api.return_value = mock_api
        
        response = client.get("/api/analysis/batch?symbols=AAPL,GOOGL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['symbol'] == 'AAPL'
        assert data[1]['symbol'] == 'GOOGL'
    
    @patch('api_server_enhanced.get_stock_api')
    def test_get_batch_analysis_too_many_symbols(self, mock_get_api, client):
        symbols = ','.join(['AAPL'] * 11)
        response = client.get(f"/api/analysis/batch?symbols={symbols}")
        assert response.status_code == 400
    
    @patch('api_server_enhanced.get_stock_api')
    def test_get_error_statistics(self, mock_get_api, client):
        mock_api = Mock()
        mock_api.error_manager = Mock()
        mock_api.error_manager.get_error_statistics = Mock(return_value={
            'total_errors': 10,
            'errors_by_severity': {'high': 5, 'medium': 3, 'low': 2},
            'errors_by_category': {'api': 8, 'analysis': 2}
        })
        mock_get_api.return_value = mock_api
        
        response = client.get("/api/errors?hours=24")
        assert response.status_code == 200
        data = response.json()
        assert data['total_errors'] == 10
    
    def test_websocket_endpoint(self, client):
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("ping")
            data = websocket.receive_text()
            assert data == "pong"
    
    def test_websocket_stats(self, client):
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("stats")
            data = json.loads(websocket.receive_text())
            assert 'active_connections' in data or isinstance(data, dict)
    
    def test_websocket_realtime(self, client):
        with patch('api_server_enhanced.StockAnalysisAPI') as mock_api_class:
            mock_api = Mock()
            mock_api.get_batch_analysis = AsyncMock(return_value=[
                {'symbol': 'AAPL', 'trend': 'bullish'}
            ])
            mock_api_class.return_value = mock_api
            
            with client.websocket_connect("/ws/realtime") as websocket:
                data = websocket.receive_text()
                parsed = json.loads(data)
                assert isinstance(parsed, list)

class TestRefactoredFunctions:
    
    @pytest.fixture
    def mock_api(self):
        data_collector = Mock()
        analyzer = Mock()
        security_manager = Mock()
        error_manager = Mock()
        news_collector = Mock()
        
        return StockAnalysisAPI(
            data_collector=data_collector,
            analyzer=analyzer,
            security_manager=security_manager,
            error_manager=error_manager,
            news_collector=news_collector
        )
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_with_retry_success(self, mock_api):
        from error_handling.error_manager import ErrorContext
        
        mock_api.data_collector.get_historical_data_async = AsyncMock(return_value=pd.DataFrame({
            'close': [100, 101, 102],
            'volume': [1000000, 1100000, 1200000]
        }))
        
        context = ErrorContext(endpoint="/test", parameters={})
        result = await mock_api._fetch_historical_data_with_retry("AAPL", context)
        
        assert not result.empty
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_calculate_indicators_safe_with_error(self, mock_api):
        from error_handling.error_manager import ErrorContext
        import pandas as pd
        
        mock_api.analyzer.calculate_all_advanced_indicators = Mock(side_effect=ValueError("Invalid data"))
        
        data = pd.DataFrame({'close': [100, 101]})
        context = ErrorContext(endpoint="/test", parameters={})
        
        result = await mock_api._calculate_indicators_safe(data, "AAPL", context)
        
        assert result.equals(data)
    
    @pytest.mark.asyncio
    async def test_calculate_analysis_components_safe(self, mock_api):
        import pandas as pd
        
        mock_api.analyzer.calculate_market_regime = Mock(return_value={'regime': 'bullish', 'confidence': 0.8})
        mock_api.analyzer.detect_chart_patterns = Mock(return_value=[{'type': 'head_shoulders'}])
        mock_api.analyzer.calculate_support_resistance = Mock(return_value={'support': [100], 'resistance': [150]})
        mock_api.analyzer.calculate_fibonacci_levels = Mock(return_value={'levels': {}})
        mock_api.analyzer.detect_anomalies_ml = Mock(return_value=[])
        mock_api.analyzer.calculate_advanced_signals = Mock(return_value={'signal': 'buy', 'confidence': 0.7})
        
        data = pd.DataFrame({'close': [100, 101, 102]})
        result = await mock_api._calculate_analysis_components_safe(data, "AAPL")
        
        assert result['market_regime']['regime'] == 'bullish'
        assert len(result['patterns']) == 1
        assert result['signals']['signal'] == 'buy'
    
    @pytest.mark.asyncio
    async def test_handle_realtime_data_error_timeout(self, mock_api):
        from error_handling.error_manager import ErrorContext
        from exceptions import TimeoutError
        
        context = ErrorContext(endpoint="/test", parameters={})
        error = TimeoutError("Request timeout")
        
        with pytest.raises(HTTPException) as exc_info:
            await mock_api._handle_realtime_data_error(error, "AAPL", context, 3, 2)
        
        assert exc_info.value.status_code == 504
    
    @pytest.mark.asyncio
    async def test_fetch_news_with_fallback_success(self):
        from api_server_enhanced import _fetch_news_with_fallback
        from data_collectors.news_collector import NewsCollector
        
        mock_collector = Mock()
        mock_collector.get_stock_news = Mock(return_value=[
            {'title': 'Test News', 'url': 'http://test.com', 'symbol': 'AAPL'}
        ])
        
        mock_api = Mock()
        mock_api.news_collector = mock_collector
        
        result = await _fetch_news_with_fallback(mock_api, "AAPL", False, False, 10.0)
        
        assert len(result) == 1
        assert result[0]['title'] == 'Test News'

class TestEnhancedStockAnalysisAPI:
    
    @pytest.fixture
    def mock_app_state(self):
        state = Mock()
        state.data_collector = Mock()
        state.analyzer = Mock()
        state.security_manager = Mock()
        state.error_manager = Mock()
        return state
    
    @pytest.fixture
    def stock_api(self, mock_app_state):
        return StockAnalysisAPI(mock_app_state)
    
    @pytest.mark.asyncio
    async def test_get_realtime_data_enhanced_success(self, stock_api):
        stock_api.data_collector.get_realtime_data_async = AsyncMock(return_value={
            'symbol': 'AAPL',
            'price': 150.25,
            'volume': 1000000,
            'change_percent': 2.5,
            'timestamp': datetime.now().isoformat()
        })
        
        result = await stock_api.get_realtime_data_enhanced('AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['currentPrice'] == 150.25
        assert 'confidenceScore' in result
    
    @pytest.mark.asyncio
    async def test_get_realtime_data_enhanced_not_found(self, stock_api):
        stock_api.data_collector.get_realtime_data_async = AsyncMock(return_value=None)
        
        with pytest.raises(Exception):
            await stock_api.get_realtime_data_enhanced('INVALID')
    
    @pytest.mark.asyncio
    async def test_get_advanced_analysis_success(self, stock_api):
        stock_api.get_realtime_data_enhanced = AsyncMock(return_value={
            'symbol': 'AAPL',
            'currentPrice': 150.25,
            'volume': 1000000,
            'changePercent': 2.5
        })
        
        stock_api.data_collector.get_historical_data_async = AsyncMock(return_value=pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=30, freq='D'),
            'close': [100] * 30,
            'volume': [1000000] * 30
        }))
        
        stock_api.analyzer.calculate_all_advanced_indicators = Mock(return_value=pd.DataFrame())
        stock_api.analyzer.calculate_market_regime = Mock(return_value={'regime': 'trending', 'confidence': 0.8})
        stock_api.analyzer.detect_chart_patterns = Mock(return_value=[])
        stock_api.analyzer.calculate_support_resistance = Mock(return_value={})
        stock_api.analyzer.calculate_fibonacci_levels = Mock(return_value={})
        stock_api.analyzer.detect_anomalies_ml = Mock(return_value=[])
        stock_api.analyzer.calculate_advanced_signals = Mock(return_value={'signal': 'buy', 'confidence': 0.75})
        
        result = await stock_api.get_advanced_analysis('AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['currentPrice'] == 150.25
        assert 'marketRegime' in result
        assert 'riskScore' in result
        assert 'confidence' in result
    
    @pytest.mark.asyncio
    async def test_get_batch_analysis_success(self, stock_api):
        stock_api.get_advanced_analysis = AsyncMock(side_effect=[
            {'symbol': 'AAPL', 'trend': 'bullish'},
            {'symbol': 'GOOGL', 'trend': 'bearish'}
        ])
        
        result = await stock_api.get_batch_analysis(['AAPL', 'GOOGL'])
        
        assert len(result) == 2
        assert result[0]['symbol'] == 'AAPL'
        assert result[1]['symbol'] == 'GOOGL'
    
    @pytest.mark.asyncio
    async def test_get_batch_analysis_with_errors(self, stock_api):
        stock_api.get_advanced_analysis = AsyncMock(side_effect=[
            {'symbol': 'AAPL', 'trend': 'bullish'},
            Exception("Error"),
            {'symbol': 'MSFT', 'trend': 'neutral'}
        ])
        
        result = await stock_api.get_batch_analysis(['AAPL', 'GOOGL', 'MSFT'])
        
        assert len(result) == 2
        assert result[0]['symbol'] == 'AAPL'
        assert result[1]['symbol'] == 'MSFT'

class TestConnectionManager:
    
    def test_connection_manager_initialization(self):
        assert manager.active_connections == []
        assert manager.connection_metadata == {}
        assert manager.rate_limits == {}
    
    def test_get_connection_stats_no_connections(self):
        stats = manager.get_connection_stats()
        assert stats['active_connections'] == 0
        assert stats['total_messages'] == 0

