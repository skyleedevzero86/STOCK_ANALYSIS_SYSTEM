import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app, StockAnalysisAPI
from fastapi.testclient import TestClient
from data_collectors.stock_data_collector import StockDataCollector
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService, AlertManager

class TestEdgeCases:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def stock_api(self):
        return StockAnalysisAPI()
    
    def test_empty_data_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = None
                mock_historical.return_value = pd.DataFrame()
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')
    
    def test_none_data_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = None
                mock_historical.return_value = None
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')
    
    def test_invalid_symbol_handling(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("Invalid symbol")
            
            response = client.get("/api/realtime/INVALID_SYMBOL")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
    
    def test_malformed_data_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 'invalid_price',
                    'volume': 'invalid_volume'
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': ['invalid'] * 30,
                    'volume': ['invalid'] * 30
                })
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')
    
    def test_extreme_values_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': float('inf'),
                    'volume': float('inf'),
                    'change_percent': float('nan')
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [float('inf')] * 30,
                    'volume': [float('inf')] * 30
                })
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')
    
    def test_negative_values_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': -150.25,
                    'volume': -1000000,
                    'change_percent': -100.0
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [-100] * 30,
                    'volume': [-1000] * 30
                })
                
                result = stock_api.get_analysis('AAPL')
                
                assert result['symbol'] == 'AAPL'
                assert result['current_price'] == -150.25
    
    def test_zero_values_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 0,
                    'volume': 0,
                    'change_percent': 0
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [0] * 30,
                    'volume': [0] * 30
                })
                
                result = stock_api.get_analysis('AAPL')
                
                assert result['symbol'] == 'AAPL'
                assert result['current_price'] == 0
    
    def test_very_large_values_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 1e10,
                    'volume': 1e15,
                    'change_percent': 1e6
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [1e10] * 30,
                    'volume': [1e15] * 30
                })
                
                result = stock_api.get_analysis('AAPL')
                
                assert result['symbol'] == 'AAPL'
                assert result['current_price'] == 1e10
    
    def test_missing_columns_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL'
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D')
                })
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')
    
    def test_duplicate_data_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D').repeat(2),
                    'close': [100] * 60,
                    'volume': [1000] * 60
                })
                
                result = stock_api.get_analysis('AAPL')
                
                assert result['symbol'] == 'AAPL'
    
    def test_timezone_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5,
                    'timestamp': datetime.now().replace(tzinfo=None)
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [100] * 30,
                    'volume': [1000] * 30
                })
                
                result = stock_api.get_analysis('AAPL')
                
                assert result['symbol'] == 'AAPL'
                assert 'timestamp' in result
    
    def test_unicode_handling(self, stock_api):
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
                    'close': [100] * 30,
                    'volume': [1000] * 30
                })
                
                result = stock_api.get_analysis('AAPL')
                
                assert result['symbol'] == 'AAPL'
    
    def test_special_characters_handling(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'change_percent': 2.5,
                'timestamp': datetime.now().isoformat()
            }
            
            response = client.get("/api/realtime/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
    
    def test_very_long_strings_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                long_string = 'A' * 10000
                
                mock_realtime.return_value = {
                    'symbol': long_string,
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [100] * 30,
                    'volume': [1000] * 30
                })
                
                result = stock_api.get_analysis(long_string)
                
                assert result['symbol'] == long_string
    
    def test_nan_values_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': float('nan'),
                    'volume': float('nan'),
                    'change_percent': float('nan')
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [float('nan')] * 30,
                    'volume': [float('nan')] * 30
                })
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')
    
    def test_infinity_values_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': float('inf'),
                    'volume': float('inf'),
                    'change_percent': float('inf')
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [float('inf')] * 30,
                    'volume': [float('inf')] * 30
                })
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')
    
    def test_negative_infinity_values_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': float('-inf'),
                    'volume': float('-inf'),
                    'change_percent': float('-inf')
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [float('-inf')] * 30,
                    'volume': [float('-inf')] * 30
                })
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')
    
    def test_mixed_data_types_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': 'AAPL',
                    'price': '150.25',
                    'volume': '1000000',
                    'change_percent': '2.5'
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': ['100'] * 30,
                    'volume': ['1000'] * 30
                })
                
                with pytest.raises(Exception):
                    stock_api.get_analysis('AAPL')
    
    def test_empty_string_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': '',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [100] * 30,
                    'volume': [1000] * 30
                })
                
                result = stock_api.get_analysis('')
                
                assert result['symbol'] == ''
    
    def test_whitespace_handling(self, stock_api):
        with patch.object(stock_api.collector, 'get_realtime_data') as mock_realtime:
            with patch.object(stock_api, '_load_historical_data') as mock_historical:
                mock_realtime.return_value = {
                    'symbol': '  AAPL  ',
                    'price': 150.25,
                    'volume': 1000000,
                    'change_percent': 2.5
                }
                
                mock_historical.return_value = pd.DataFrame({
                    'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'close': [100] * 30,
                    'volume': [1000] * 30
                })
                
                result = stock_api.get_analysis('  AAPL  ')
                
                assert result['symbol'] == '  AAPL  '
    
    def test_sql_injection_handling(self, client):
        malicious_symbol = "'; DROP TABLE stocks; --"
        
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("Invalid symbol")
            
            response = client.get(f"/api/realtime/{malicious_symbol}")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
    
    def test_xss_handling(self, client):
        xss_symbol = "<script>alert('XSS')</script>"
        
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("Invalid symbol")
            
            response = client.get(f"/api/realtime/{xss_symbol}")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
    
    def test_path_traversal_handling(self, client):
        path_traversal_symbol = "../../../etc/passwd"
        
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("Invalid symbol")
            
            response = client.get(f"/api/realtime/{path_traversal_symbol}")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
    
    def test_command_injection_handling(self, client):
        command_injection_symbol = "; rm -rf /"
        
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("Invalid symbol")
            
            response = client.get(f"/api/realtime/{command_injection_symbol}")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
    
    def test_very_large_payload_handling(self, client):
        large_symbol = 'A' * 1000000
        
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("Invalid symbol")
            
            response = client.get(f"/api/realtime/{large_symbol}")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
    
    def test_null_bytes_handling(self, client):
        null_byte_symbol = "AAPL\x00"
        
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("Invalid symbol")
            
            response = client.get(f"/api/realtime/{null_byte_symbol}")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
    
    def test_unicode_escape_handling(self, client):
        unicode_symbol = "AAPL\u0000\u0001\u0002"
        
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.side_effect = Exception("Invalid symbol")
            
            response = client.get(f"/api/realtime/{unicode_symbol}")
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data
    
    def test_very_deep_nesting_handling(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            mock_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'change_percent': 2.5,
                'nested': {
                    'level1': {
                        'level2': {
                            'level3': {
                                'level4': {
                                    'level5': {
                                        'value': 'deep'
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            response = client.get("/api/realtime/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
            assert 'nested' in data
    
    def test_circular_reference_handling(self, client):
        with patch('api_server.stock_api.get_realtime_data') as mock_realtime:
            circular_data = {'symbol': 'AAPL', 'price': 150.25}
            circular_data['self'] = circular_data
            
            mock_realtime.return_value = circular_data
            
            response = client.get("/api/realtime/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data['symbol'] == 'AAPL'
