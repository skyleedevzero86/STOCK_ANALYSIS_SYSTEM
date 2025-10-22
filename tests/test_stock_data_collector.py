import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.stock_data_collector import StockDataCollector, DataQualityChecker

class TestStockDataCollector:
    
    @pytest.fixture
    def collector(self):
        return StockDataCollector(['AAPL', 'GOOGL', 'MSFT'])
    
    @pytest.fixture
    def sample_historical_data(self):
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        np.random.seed(42)
        
        return pd.DataFrame({
            'date': dates,
            'close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'volume': np.random.randint(1000000, 5000000, len(dates)),
            'symbol': 'AAPL'
        })
    
    def test_initialization(self, collector):
        assert collector.symbols == ['AAPL', 'GOOGL', 'MSFT']
        assert collector.session is not None
    
    def test_get_historical_data_structure(self, collector):
        data = collector.get_historical_data('AAPL', period='1mo')
        
        if not data.empty:
            expected_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']
            for col in expected_columns:
                assert col in data.columns
            
            assert data['symbol'].iloc[0] == 'AAPL'
            assert len(data) > 0
    
    def test_get_realtime_data_structure(self, collector):
        data = collector.get_realtime_data('AAPL')
        
        if data:
            expected_keys = ['symbol', 'timestamp', 'price', 'volume', 'change', 'change_percent']
            for key in expected_keys:
                assert key in data
            
            assert data['symbol'] == 'AAPL'
            assert isinstance(data['price'], (int, float))
            assert isinstance(data['volume'], (int, float))
            assert isinstance(data['timestamp'], datetime)
    
    def test_get_multiple_realtime_data(self, collector):
        results = collector.get_multiple_realtime_data()
        
        assert isinstance(results, list)
        assert len(results) <= len(collector.symbols)
        
        for data in results:
            if data:
                assert 'symbol' in data
                assert 'price' in data
                assert 'timestamp' in data
    
    def test_collect_batch_data(self, collector):
        all_data = collector.collect_batch_data()
        
        assert isinstance(all_data, dict)
        for symbol, data in all_data.items():
            assert symbol in collector.symbols
            assert isinstance(data, pd.DataFrame)
            assert not data.empty
            assert 'close' in data.columns
            assert 'volume' in data.columns
    
    def test_alpha_vantage_data_structure(self, collector):
        api_key = "test_key"
        data = collector.get_alpha_vantage_data('AAPL', api_key)
        
        if data:
            expected_keys = ['symbol', 'price', 'change', 'change_percent', 'volume', 'high', 'low', 'open']
            for key in expected_keys:
                assert key in data
            
            assert data['symbol'] == 'AAPL'
            assert isinstance(data['price'], (int, float))
            assert isinstance(data['volume'], (int, float))

class TestDataQualityChecker:
    
    @pytest.fixture
    def checker(self):
        return DataQualityChecker()
    
    @pytest.fixture
    def good_data(self):
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        return pd.DataFrame({
            'date': dates,
            'close': 100 + np.random.randn(len(dates)) * 2,
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })
    
    @pytest.fixture
    def bad_data(self):
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        return pd.DataFrame({
            'date': dates,
            'close': [0, -10, 50, 0, 100, 0, 75, 0, 90, 0],
            'volume': [0, 1000, 0, 2000, 0, 3000, 0, 4000, 0, 5000]
        })
    
    def test_check_data_completeness_good_data(self, checker, good_data):
        result = checker.check_data_completeness(good_data, 'AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['is_valid'] is True
        assert result['data_quality_score'] >= 0.7
        assert len(result['issues']) == 0
    
    def test_check_data_completeness_bad_data(self, checker, bad_data):
        result = checker.check_data_completeness(bad_data, 'AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['is_valid'] is False
        assert result['data_quality_score'] < 0.7
        assert len(result['issues']) > 0
    
    def test_check_data_completeness_empty_data(self, checker):
        empty_data = pd.DataFrame()
        result = checker.check_data_completeness(empty_data, 'AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['is_valid'] is False
        assert result['data_quality_score'] == 0.0
        assert '데이터 없음' in result['issues']
    
    def test_detect_outliers(self, checker, good_data):
        result = checker.detect_outliers(good_data, 'AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert 'outliers' in result
        assert 'outlier_count' in result
        assert 'outlier_percentage' in result
        assert isinstance(result['outliers'], list)
        assert isinstance(result['outlier_count'], int)
        assert isinstance(result['outlier_percentage'], float)
    
    def test_detect_outliers_empty_data(self, checker):
        empty_data = pd.DataFrame()
        result = checker.detect_outliers(empty_data, 'AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['outliers'] == []
        assert result['outlier_count'] == 0
    
    def test_detect_outliers_no_close_column(self, checker):
        data_without_close = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=10, freq='D'),
            'volume': np.random.randint(1000, 5000, 10)
        })
        
        result = checker.detect_outliers(data_without_close, 'AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['outliers'] == []
        assert result['outlier_count'] == 0
    
    def test_zero_prices_quality_impact(self, checker):
        data_with_zero_prices = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100] * 25 + [0] * 5,
            'volume': np.random.randint(1000000, 5000000, 30)
        })
        
        result = checker.check_data_completeness(data_with_zero_prices, 'AAPL')
        
        assert result['data_quality_score'] < 1.0
        assert any('0 또는 음수 가격' in issue for issue in result['issues'])
    
    def test_missing_days_calculation(self, checker):
        short_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=10, freq='D'),
            'close': np.random.randn(10) * 2 + 100,
            'volume': np.random.randint(1000000, 5000000, 10)
        })
        
        result = checker.check_data_completeness(short_data, 'AAPL')
        
        assert result['missing_days'] > 0
        assert any('일 데이터 누락' in issue for issue in result['issues'])
