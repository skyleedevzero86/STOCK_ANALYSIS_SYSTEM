import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_engine.technical_analyzer import TechnicalAnalyzer

class TestTechnicalAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        return TechnicalAnalyzer()
    
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        np.random.seed(42)
        
        return pd.DataFrame({
            'date': dates,
            'close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })
    
    def test_calculate_rsi(self, analyzer, sample_data):
        rsi = analyzer.calculate_rsi(sample_data)
        
        assert not rsi.empty
        assert len(rsi) == len(sample_data)
        assert all(0 <= val <= 100 for val in rsi.dropna())
    
    def test_calculate_macd(self, analyzer, sample_data):
        macd_data = analyzer.calculate_macd(sample_data)
        
        assert 'macd' in macd_data
        assert 'macd_signal' in macd_data
        assert 'macd_histogram' in macd_data
        assert not macd_data['macd'].empty
        assert not macd_data['macd_signal'].empty
        assert not macd_data['macd_histogram'].empty
    
    def test_calculate_bollinger_bands(self, analyzer, sample_data):
        bb_data = analyzer.calculate_bollinger_bands(sample_data)
        
        assert 'bb_upper' in bb_data
        assert 'bb_middle' in bb_data
        assert 'bb_lower' in bb_data
        assert not bb_data['bb_upper'].empty
        assert not bb_data['bb_middle'].empty
        assert not bb_data['bb_lower'].empty
        
        for i in range(len(bb_data['bb_upper'])):
            if not pd.isna(bb_data['bb_upper'].iloc[i]):
                assert bb_data['bb_upper'].iloc[i] >= bb_data['bb_middle'].iloc[i]
                assert bb_data['bb_middle'].iloc[i] >= bb_data['bb_lower'].iloc[i]
    
    def test_calculate_moving_averages(self, analyzer, sample_data):
        ma_data = analyzer.calculate_moving_averages(sample_data)
        
        assert 'sma_20' in ma_data
        assert 'sma_50' in ma_data
        assert 'ema_12' in ma_data
        assert 'ema_26' in ma_data
        assert not ma_data['sma_20'].empty
        assert not ma_data['sma_50'].empty
        assert not ma_data['ema_12'].empty
        assert not ma_data['ema_26'].empty
    
    def test_calculate_all_indicators(self, analyzer, sample_data):
        analyzed_data = analyzer.calculate_all_indicators(sample_data)
        
        expected_columns = ['rsi_14', 'macd', 'macd_signal', 'macd_histogram', 
                           'bb_upper', 'bb_middle', 'bb_lower', 'sma_20', 'sma_50']
        
        for col in expected_columns:
            assert col in analyzed_data.columns
            assert not analyzed_data[col].empty
    
    def test_analyze_trend(self, analyzer, sample_data):
        analyzed_data = analyzer.calculate_all_indicators(sample_data)
        trend_analysis = analyzer.analyze_trend(analyzed_data)
        
        assert 'trend' in trend_analysis
        assert 'strength' in trend_analysis
        assert 'signals' in trend_analysis
        assert trend_analysis['trend'] in ['bullish', 'bearish', 'neutral']
        assert 0 <= trend_analysis['strength'] <= 1
        assert isinstance(trend_analysis['signals'], list)
    
    def test_detect_anomalies(self, analyzer, sample_data):
        analyzed_data = analyzer.calculate_all_indicators(sample_data)
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        
        assert isinstance(anomalies, list)
        for anomaly in anomalies:
            assert 'type' in anomaly
            assert 'severity' in anomaly
            assert 'message' in anomaly
            assert anomaly['severity'] in ['low', 'medium', 'high']
    
    def test_generate_signals(self, analyzer, sample_data):
        analyzed_data = analyzer.calculate_all_indicators(sample_data)
        signals = analyzer.generate_signals(analyzed_data, 'TEST')
        
        assert 'signal' in signals
        assert 'confidence' in signals
        assert 'signals' in signals
        assert 'reason' in signals
        assert signals['signal'] in ['buy', 'sell', 'hold']
        assert 0 <= signals['confidence'] <= 1
        assert isinstance(signals['signals'], list)
    
    def test_empty_data_handling(self, analyzer):
        empty_data = pd.DataFrame()
        
        trend_analysis = analyzer.analyze_trend(empty_data)
        assert trend_analysis['trend'] == 'unknown'
        assert trend_analysis['strength'] == 0
        
        anomalies = analyzer.detect_anomalies(empty_data, 'TEST')
        assert anomalies == []
        
        signals = analyzer.generate_signals(empty_data, 'TEST')
        assert signals['signal'] == 'hold'
        assert signals['confidence'] == 0
    
    def test_insufficient_data_handling(self, analyzer):
        insufficient_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5, freq='D'),
            'close': [100, 101, 102, 103, 104],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        analyzed_data = analyzer.calculate_all_indicators(insufficient_data)
        assert analyzed_data.equals(insufficient_data)
        
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        assert anomalies == []
        
        signals = analyzer.generate_signals(analyzed_data, 'TEST')
        assert signals['signal'] == 'hold'
        assert signals['confidence'] == 0
    
    def test_rsi_extreme_values(self, analyzer):
        extreme_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100] * 30,
            'volume': [1000] * 30
        })
        
        analyzed_data = analyzer.calculate_all_indicators(extreme_data)
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        
        assert isinstance(anomalies, list)
    
    def test_volume_spike_detection(self, analyzer):
        spike_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100] * 30,
            'volume': [1000] * 29 + [10000000]
        })
        
        analyzed_data = analyzer.calculate_all_indicators(spike_data)
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        
        volume_spikes = [a for a in anomalies if a['type'] == 'volume_spike']
        assert len(volume_spikes) > 0
        assert volume_spikes[0]['severity'] == 'high'
    
    def test_price_spike_detection(self, analyzer):
        spike_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'close': [100] * 29 + [110],
            'volume': [1000] * 30
        })
        
        analyzed_data = analyzer.calculate_all_indicators(spike_data)
        anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
        
        price_spikes = [a for a in anomalies if a['type'] == 'price_spike']
        assert len(price_spikes) > 0
        assert price_spikes[0]['severity'] in ['medium', 'high']
