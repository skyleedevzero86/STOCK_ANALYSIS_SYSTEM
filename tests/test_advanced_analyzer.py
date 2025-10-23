import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_engine.advanced_analyzer import AdvancedAnalyzer

class TestAdvancedAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        return AdvancedAnalyzer()
    
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        return pd.DataFrame({
            'date': dates,
            'open': 100 + np.random.randn(len(dates)) * 2,
            'high': 105 + np.random.randn(len(dates)) * 2,
            'low': 95 + np.random.randn(len(dates)) * 2,
            'close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })
    
    def test_initialization(self, analyzer):
        assert analyzer is not None
        assert hasattr(analyzer, 'calculate_advanced_indicators')
        assert hasattr(analyzer, 'detect_market_regimes')
        assert hasattr(analyzer, 'analyze_correlation')
        assert hasattr(analyzer, 'generate_portfolio_signals')
    
    def test_calculate_advanced_indicators(self, analyzer, sample_data):
        result = analyzer.calculate_advanced_indicators(sample_data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)
        
        expected_columns = ['atr', 'stoch', 'williams_r', 'cci', 'adx', 'obv', 'mfi']
        for col in expected_columns:
            assert col in result.columns
            assert not result[col].empty
    
    def test_detect_market_regimes(self, analyzer, sample_data):
        analyzed_data = analyzer.calculate_advanced_indicators(sample_data)
        regimes = analyzer.detect_market_regimes(analyzed_data)
        
        assert isinstance(regimes, dict)
        assert 'current_regime' in regimes
        assert 'regime_strength' in regimes
        assert 'regime_duration' in regimes
        assert 'regime_transitions' in regimes
        
        assert regimes['current_regime'] in ['bull_market', 'bear_market', 'sideways', 'volatile']
        assert 0 <= regimes['regime_strength'] <= 1
        assert isinstance(regimes['regime_duration'], int)
        assert isinstance(regimes['regime_transitions'], list)
    
    def test_analyze_correlation(self, analyzer, sample_data):
        correlation_data = analyzer.analyze_correlation(sample_data)
        
        assert isinstance(correlation_data, dict)
        assert 'price_volume_correlation' in correlation_data
        assert 'volatility_correlation' in correlation_data
        assert 'trend_correlation' in correlation_data
        
        assert -1 <= correlation_data['price_volume_correlation'] <= 1
        assert -1 <= correlation_data['volatility_correlation'] <= 1
        assert -1 <= correlation_data['trend_correlation'] <= 1
    
    def test_generate_portfolio_signals(self, analyzer, sample_data):
        analyzed_data = analyzer.calculate_advanced_indicators(sample_data)
        signals = analyzer.generate_portfolio_signals(analyzed_data, 'TEST')
        
        assert isinstance(signals, dict)
        assert 'portfolio_signal' in signals
        assert 'risk_level' in signals
        assert 'diversification_score' in signals
        assert 'correlation_risk' in signals
        
        assert signals['portfolio_signal'] in ['buy', 'sell', 'hold', 'reduce']
        assert signals['risk_level'] in ['low', 'medium', 'high', 'very_high']
        assert 0 <= signals['diversification_score'] <= 1
        assert 0 <= signals['correlation_risk'] <= 1
    
    def test_empty_data_handling(self, analyzer):
        empty_data = pd.DataFrame()
        
        result = analyzer.calculate_advanced_indicators(empty_data)
        assert result.empty
        
        regimes = analyzer.detect_market_regimes(empty_data)
        assert regimes['current_regime'] == 'unknown'
        assert regimes['regime_strength'] == 0
        
        correlation = analyzer.analyze_correlation(empty_data)
        assert correlation['price_volume_correlation'] == 0
        
        signals = analyzer.generate_portfolio_signals(empty_data, 'TEST')
        assert signals['portfolio_signal'] == 'hold'
    
    def test_insufficient_data_handling(self, analyzer):
        insufficient_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5, freq='D'),
            'close': [100, 101, 102, 103, 104],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        result = analyzer.calculate_advanced_indicators(insufficient_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert regimes['current_regime'] == 'unknown'
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert signals['portfolio_signal'] == 'hold'
    
    def test_extreme_values_handling(self, analyzer):
        extreme_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': [100] * 50,
            'high': [200] * 50,
            'low': [50] * 50,
            'close': [100] * 50,
            'volume': [10000000] * 50
        })
        
        result = analyzer.calculate_advanced_indicators(extreme_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert regimes['current_regime'] in ['bull_market', 'bear_market', 'sideways', 'volatile']
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert signals['portfolio_signal'] in ['buy', 'sell', 'hold', 'reduce']
    
    def test_missing_columns_handling(self, analyzer):
        incomplete_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'close': [100 + i for i in range(50)]
        })
        
        result = analyzer.calculate_advanced_indicators(incomplete_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert isinstance(regimes, dict)
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert isinstance(signals, dict)
    
    def test_nan_values_handling(self, analyzer):
        nan_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': [100] * 25 + [np.nan] * 25,
            'high': [105] * 25 + [np.nan] * 25,
            'low': [95] * 25 + [np.nan] * 25,
            'close': [100] * 25 + [np.nan] * 25,
            'volume': [1000] * 25 + [np.nan] * 25
        })
        
        result = analyzer.calculate_advanced_indicators(nan_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert isinstance(regimes, dict)
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert isinstance(signals, dict)
    
    def test_negative_values_handling(self, analyzer):
        negative_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': [-100] * 50,
            'high': [-95] * 50,
            'low': [-105] * 50,
            'close': [-100] * 50,
            'volume': [1000] * 50
        })
        
        result = analyzer.calculate_advanced_indicators(negative_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert isinstance(regimes, dict)
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert isinstance(signals, dict)
    
    def test_zero_values_handling(self, analyzer):
        zero_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': [0] * 50,
            'high': [0] * 50,
            'low': [0] * 50,
            'close': [0] * 50,
            'volume': [0] * 50
        })
        
        result = analyzer.calculate_advanced_indicators(zero_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert isinstance(regimes, dict)
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert isinstance(signals, dict)
    
    def test_very_large_dataset(self, analyzer):
        large_data = pd.DataFrame({
            'date': pd.date_range(start='2020-01-01', periods=1000, freq='D'),
            'open': 100 + np.random.randn(1000) * 2,
            'high': 105 + np.random.randn(1000) * 2,
            'low': 95 + np.random.randn(1000) * 2,
            'close': 100 + np.cumsum(np.random.randn(1000) * 0.5),
            'volume': np.random.randint(1000000, 5000000, 1000)
        })
        
        result = analyzer.calculate_advanced_indicators(large_data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(large_data)
        
        regimes = analyzer.detect_market_regimes(result)
        assert isinstance(regimes, dict)
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert isinstance(signals, dict)
    
    def test_constant_values_handling(self, analyzer):
        constant_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': [100] * 50,
            'high': [100] * 50,
            'low': [100] * 50,
            'close': [100] * 50,
            'volume': [1000] * 50
        })
        
        result = analyzer.calculate_advanced_indicators(constant_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert regimes['current_regime'] == 'sideways'
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert signals['portfolio_signal'] == 'hold'
    
    def test_volatile_data_handling(self, analyzer):
        volatile_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': 100 + np.random.randn(50) * 10,
            'high': 105 + np.random.randn(50) * 10,
            'low': 95 + np.random.randn(50) * 10,
            'close': 100 + np.random.randn(50) * 10,
            'volume': np.random.randint(1000000, 10000000, 50)
        })
        
        result = analyzer.calculate_advanced_indicators(volatile_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert regimes['current_regime'] in ['volatile', 'sideways']
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert signals['risk_level'] in ['high', 'very_high']
    
    def test_trending_data_handling(self, analyzer):
        trending_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': [100 + i for i in range(50)],
            'high': [105 + i for i in range(50)],
            'low': [95 + i for i in range(50)],
            'close': [100 + i for i in range(50)],
            'volume': [1000 + i * 10 for i in range(50)]
        })
        
        result = analyzer.calculate_advanced_indicators(trending_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert regimes['current_regime'] == 'bull_market'
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert signals['portfolio_signal'] in ['buy', 'hold']
    
    def test_reversing_data_handling(self, analyzer):
        reversing_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': [100 + i if i < 25 else 125 - (i - 25) for i in range(50)],
            'high': [105 + i if i < 25 else 130 - (i - 25) for i in range(50)],
            'low': [95 + i if i < 25 else 120 - (i - 25) for i in range(50)],
            'close': [100 + i if i < 25 else 125 - (i - 25) for i in range(50)],
            'volume': [1000 + i * 10 for i in range(50)]
        })
        
        result = analyzer.calculate_advanced_indicators(reversing_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert regimes['current_regime'] in ['bull_market', 'bear_market', 'volatile']
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert signals['portfolio_signal'] in ['buy', 'sell', 'hold', 'reduce']
    
    def test_seasonal_data_handling(self, analyzer):
        seasonal_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
            'open': 100 + 10 * np.sin(np.arange(100) * 2 * np.pi / 30),
            'high': 105 + 10 * np.sin(np.arange(100) * 2 * np.pi / 30),
            'low': 95 + 10 * np.sin(np.arange(100) * 2 * np.pi / 30),
            'close': 100 + 10 * np.sin(np.arange(100) * 2 * np.pi / 30),
            'volume': 1000 + 100 * np.sin(np.arange(100) * 2 * np.pi / 30)
        })
        
        result = analyzer.calculate_advanced_indicators(seasonal_data)
        assert isinstance(result, pd.DataFrame)
        
        regimes = analyzer.detect_market_regimes(result)
        assert isinstance(regimes, dict)
        
        signals = analyzer.generate_portfolio_signals(result, 'TEST')
        assert isinstance(signals, dict)
    
    def test_correlation_analysis_edge_cases(self, analyzer):
        uncorrelated_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': np.random.randn(50) * 10 + 100,
            'high': np.random.randn(50) * 10 + 105,
            'low': np.random.randn(50) * 10 + 95,
            'close': np.random.randn(50) * 10 + 100,
            'volume': np.random.randint(1000000, 5000000, 50)
        })
        
        correlation = analyzer.analyze_correlation(uncorrelated_data)
        assert isinstance(correlation, dict)
        assert 'price_volume_correlation' in correlation
        assert 'volatility_correlation' in correlation
        assert 'trend_correlation' in correlation
        
        assert -1 <= correlation['price_volume_correlation'] <= 1
        assert -1 <= correlation['volatility_correlation'] <= 1
        assert -1 <= correlation['trend_correlation'] <= 1
    
    def test_portfolio_signals_edge_cases(self, analyzer):
        high_risk_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
            'open': 100 + np.random.randn(50) * 20,
            'high': 105 + np.random.randn(50) * 20,
            'low': 95 + np.random.randn(50) * 20,
            'close': 100 + np.random.randn(50) * 20,
            'volume': np.random.randint(1000000, 10000000, 50)
        })
        
        analyzed_data = analyzer.calculate_advanced_indicators(high_risk_data)
        signals = analyzer.generate_portfolio_signals(analyzed_data, 'TEST')
        
        assert isinstance(signals, dict)
        assert 'portfolio_signal' in signals
        assert 'risk_level' in signals
        assert 'diversification_score' in signals
        assert 'correlation_risk' in signals
        
        assert signals['portfolio_signal'] in ['buy', 'sell', 'hold', 'reduce']
        assert signals['risk_level'] in ['low', 'medium', 'high', 'very_high']
        assert 0 <= signals['diversification_score'] <= 1
        assert 0 <= signals['correlation_risk'] <= 1
