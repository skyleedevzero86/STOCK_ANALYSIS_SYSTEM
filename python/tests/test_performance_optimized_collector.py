import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.performance_optimized_collector import PerformanceOptimizedCollector

class TestPerformanceOptimizedCollector:
    
    @pytest.fixture
    def collector(self):
        return PerformanceOptimizedCollector(['AAPL', 'GOOGL', 'MSFT'], use_mock_data=True)
    
    def test_initialization(self, collector):
        assert collector.symbols == ['AAPL', 'GOOGL', 'MSFT']
        assert collector.use_mock_data is True
        assert hasattr(collector, 'cache')
        assert hasattr(collector, 'rate_limiter')
        assert hasattr(collector, 'batch_processor')
    
    def test_caching_mechanism(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'timestamp': datetime.now()
            }
            
            result1 = collector.get_cached_realtime_data('AAPL')
            result2 = collector.get_cached_realtime_data('AAPL')
            
            assert result1 == result2
            mock_get_realtime.assert_called_once()
    
    def test_rate_limiting(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'timestamp': datetime.now()
            }
            
            start_time = time.time()
            for _ in range(10):
                collector.get_rate_limited_data('AAPL')
            end_time = time.time()
            
            assert end_time - start_time >= 1.0
            assert mock_get_realtime.call_count == 10
    
    def test_batch_processing(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'timestamp': datetime.now()
            }
            
            results = collector.process_batch(['AAPL', 'GOOGL', 'MSFT'])
            
            assert isinstance(results, list)
            assert len(results) == 3
            assert all(result['symbol'] in ['AAPL', 'GOOGL', 'MSFT'] for result in results)
    
    def test_parallel_processing(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'timestamp': datetime.now()
            }
            
            start_time = time.time()
            results = collector.get_parallel_data(['AAPL', 'GOOGL', 'MSFT'])
            end_time = time.time()
            
            assert isinstance(results, list)
            assert len(results) == 3
            assert end_time - start_time < 2.0
    
    def test_memory_optimization(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            for i in range(10):
                data = collector.get_optimized_historical_data('AAPL', period='1y')
                assert isinstance(data, pd.DataFrame)
                assert not data.empty
                
                if i % 3 == 0:
                    collector.clear_cache()
    
    def test_error_handling(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.side_effect = Exception("API Error")
            
            result = collector.get_realtime_data_with_fallback('AAPL')
            
            assert result is None or result == {}
    
    def test_fallback_mechanism(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            with patch.object(collector, 'get_mock_data') as mock_mock_data:
                mock_get_realtime.side_effect = Exception("API Error")
                mock_mock_data.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.25,
                    'volume': 1000000,
                    'timestamp': datetime.now()
                }
                
                result = collector.get_realtime_data_with_fallback('AAPL')
                
                assert result is not None
                assert result['symbol'] == 'AAPL'
    
    def test_data_validation(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.return_value = {
                'symbol': 'AAPL',
                'price': -150.25,
                'volume': -1000000,
                'timestamp': datetime.now()
            }
            
            result = collector.get_validated_data('AAPL')
            
            assert result is None or result == {}
    
    def test_data_cleaning(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'timestamp': datetime.now(),
                'extra_field': 'unnecessary'
            }
            
            result = collector.get_cleaned_data('AAPL')
            
            assert 'extra_field' not in result
            assert 'symbol' in result
            assert 'price' in result
            assert 'volume' in result
            assert 'timestamp' in result
    
    def test_concurrent_access(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'timestamp': datetime.now()
            }
            
            def get_data():
                return collector.get_cached_realtime_data('AAPL')
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(get_data) for _ in range(10)]
                results = [future.result() for future in as_completed(futures)]
            
            assert len(results) == 10
            assert all(result['symbol'] == 'AAPL' for result in results)
    
    def test_cache_expiration(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'timestamp': datetime.now()
            }
            
            result1 = collector.get_cached_realtime_data('AAPL')
            time.sleep(2)
            result2 = collector.get_cached_realtime_data('AAPL')
            
            assert result1 == result2
            assert mock_get_realtime.call_count == 1
    
    def test_memory_usage_monitoring(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            memory_usage = collector.get_memory_usage()
            assert isinstance(memory_usage, dict)
            assert 'current_usage' in memory_usage
            assert 'peak_usage' in memory_usage
            assert 'cache_size' in memory_usage
    
    def test_performance_metrics(self, collector):
        with patch.object(collector, 'get_realtime_data') as mock_get_realtime:
            mock_get_realtime.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'timestamp': datetime.now()
            }
            
            for _ in range(5):
                collector.get_cached_realtime_data('AAPL')
            
            metrics = collector.get_performance_metrics()
            assert isinstance(metrics, dict)
            assert 'total_requests' in metrics
            assert 'cache_hits' in metrics
            assert 'cache_misses' in metrics
            assert 'average_response_time' in metrics
    
    def test_data_compression(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            compressed_data = collector.get_compressed_data('AAPL', period='1y')
            assert isinstance(compressed_data, pd.DataFrame)
            assert not compressed_data.empty
    
    def test_data_aggregation(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            aggregated_data = collector.get_aggregated_data('AAPL', period='1y', aggregation='weekly')
            assert isinstance(aggregated_data, pd.DataFrame)
            assert not aggregated_data.empty
    
    def test_data_filtering(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            filtered_data = collector.get_filtered_data('AAPL', filters={'volume': '>5000000'})
            assert isinstance(filtered_data, pd.DataFrame)
            assert not filtered_data.empty
    
    def test_data_sorting(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            sorted_data = collector.get_sorted_data('AAPL', sort_by='volume', ascending=False)
            assert isinstance(sorted_data, pd.DataFrame)
            assert not sorted_data.empty
            assert sorted_data['volume'].iloc[0] >= sorted_data['volume'].iloc[-1]
    
    def test_data_grouping(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            grouped_data = collector.get_grouped_data('AAPL', group_by='month')
            assert isinstance(grouped_data, pd.DataFrame)
            assert not grouped_data.empty
    
    def test_data_statistics(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            statistics = collector.get_data_statistics('AAPL')
            assert isinstance(statistics, dict)
            assert 'mean' in statistics
            assert 'std' in statistics
            assert 'min' in statistics
            assert 'max' in statistics
            assert 'median' in statistics
    
    def test_data_correlation(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            correlation = collector.get_data_correlation('AAPL', 'GOOGL')
            assert isinstance(correlation, dict)
            assert 'correlation_coefficient' in correlation
            assert 'p_value' in correlation
            assert 'significance' in correlation
    
    def test_data_trend(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            trend = collector.get_data_trend('AAPL')
            assert isinstance(trend, dict)
            assert 'trend_direction' in trend
            assert 'trend_strength' in trend
            assert 'trend_duration' in trend
    
    def test_data_volatility(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            volatility = collector.get_data_volatility('AAPL')
            assert isinstance(volatility, dict)
            assert 'volatility' in volatility
            assert 'volatility_percentile' in volatility
            assert 'volatility_trend' in volatility
    
    def test_data_momentum(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            momentum = collector.get_data_momentum('AAPL')
            assert isinstance(momentum, dict)
            assert 'momentum' in momentum
            assert 'momentum_strength' in momentum
            assert 'momentum_direction' in momentum
    
    def test_data_anomalies(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            anomalies = collector.get_data_anomalies('AAPL')
            assert isinstance(anomalies, list)
            for anomaly in anomalies:
                assert 'type' in anomaly
                assert 'severity' in anomaly
                assert 'timestamp' in anomaly
                assert 'description' in anomaly
    
    def test_data_quality(self, collector):
        with patch.object(collector, 'get_historical_data') as mock_get_historical:
            mock_get_historical.return_value = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=1000, freq='D'),
                'close': np.random.randn(1000) * 100 + 1000,
                'volume': np.random.randint(1000000, 10000000, 1000)
            })
            
            quality = collector.get_data_quality('AAPL')
            assert isinstance(quality, dict)
            assert 'completeness' in quality
            assert 'accuracy' in quality
            assert 'consistency' in quality
            assert 'timeliness' in quality
            assert 'validity' in quality
