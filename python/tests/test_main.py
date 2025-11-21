import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import StockAnalysisSystem

class TestStockAnalysisSystem:
    
    @pytest.fixture
    def system(self):
        with patch('main.StockDataCollector'):
            with patch('main.TechnicalAnalyzer'):
                with patch('main.NotificationService'):
                    with patch('main.AlertManager'):
                        with patch('main.settings'):
                            return StockAnalysisSystem()
    
    def test_initialization(self, system):
        assert system.symbols is not None
        assert system.collector is not None
        assert system.analyzer is not None
        assert system.notification_service is not None
        assert system.alert_manager is not None
    
    @patch('main.StockDataCollector')
    @patch('main.TechnicalAnalyzer')
    @patch('main.NotificationService')
    @patch('main.AlertManager')
    def test_run_analysis_cycle_success(self, mock_alert, mock_notif, mock_analyzer, mock_collector, system):
        mock_collector_instance = Mock()
        mock_collector_instance.get_multiple_realtime_data.return_value = [
            {
                'symbol': 'AAPL',
                'price': 150.25,
                'volume': 1000000,
                'change_percent': 2.5
            }
        ]
        system.collector = mock_collector_instance
        
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.calculate_all_indicators.return_value = Mock()
        mock_analyzer_instance.analyze_trend.return_value = {
            'trend': 'bullish',
            'strength': 0.8
        }
        mock_analyzer_instance.detect_anomalies.return_value = []
        mock_analyzer_instance.generate_signals.return_value = {
            'signal': 'buy',
            'confidence': 0.75
        }
        system.analyzer = mock_analyzer_instance
        
        system._load_historical_data = Mock(return_value=Mock())
        system._load_historical_data.return_value.empty = False
        
        result = system.run_analysis_cycle()
        
        assert result['status'] == 'success'
        assert 'symbols_analyzed' in result
        assert 'timestamp' in result
    
    def test_run_analysis_cycle_no_data(self, system):
        system.collector = Mock()
        system.collector.get_multiple_realtime_data.return_value = []
        
        result = system.run_analysis_cycle()
        
        assert result['status'] == 'failed'
        assert result['reason'] == 'no_data'
    
    def test_run_analysis_cycle_exception(self, system):
        system.collector = Mock()
        system.collector.get_multiple_realtime_data.side_effect = Exception("Test error")
        
        result = system.run_analysis_cycle()
        
        assert result['status'] == 'failed'
        assert 'reason' in result
    
    @patch('main.pd')
    @patch('main.np')
    def test_load_historical_data(self, mock_np, mock_pd, system):
        import pandas as pd
        import numpy as np
        
        mock_pd.date_range.return_value = pd.date_range('2024-01-01', periods=30, freq='D')
        mock_np.random.seed = Mock()
        mock_np.random.randn.return_value = np.random.randn(30)
        mock_np.cumsum.return_value = np.cumsum(np.random.randn(30))
        mock_np.random.randint.return_value = np.random.randint(1000000, 5000000, 30)
        
        result = system._load_historical_data('AAPL')
        
        assert result is not None
        assert 'date' in result.columns
        assert 'close' in result.columns
        assert 'volume' in result.columns
    
    def test_process_notifications(self, system):
        system.alert_manager = Mock()
        system.alert_manager.process_anomaly_alerts.return_value = {'alerts_sent': 2}
        system.alert_manager.process_analysis_reports.return_value = {'reports_sent': 1}
        
        analysis_results = [
            {
                'symbol': 'AAPL',
                'anomalies': [
                    {'type': 'volume_spike', 'severity': 'high'}
                ]
            }
        ]
        
        result = system._process_notifications(analysis_results)
        
        assert result['total_sent'] == 3
        assert result['anomaly_alerts'] == 2
        assert result['reports_sent'] == 1
    
    def test_process_notifications_no_anomalies(self, system):
        system.alert_manager = Mock()
        system.alert_manager.process_analysis_reports.return_value = {'reports_sent': 1}
        
        analysis_results = [
            {
                'symbol': 'AAPL',
                'anomalies': []
            }
        ]
        
        result = system._process_notifications(analysis_results)
        
        assert result['total_sent'] == 1
        assert result['anomaly_alerts'] == 0
    
    def test_process_notifications_exception(self, system):
        system.alert_manager = Mock()
        system.alert_manager.process_anomaly_alerts.side_effect = Exception("Error")
        
        analysis_results = [
            {
                'symbol': 'AAPL',
                'anomalies': [{'type': 'volume_spike', 'severity': 'high'}]
            }
        ]
        
        result = system._process_notifications(analysis_results)
        
        assert result['total_sent'] == 0
    
    def test_save_analysis_results(self, system):
        analysis_results = [
            {
                'symbol': 'AAPL',
                'trend': 'bullish',
                'signals': {
                    'signal': 'buy',
                    'confidence': 0.75
                }
            },
            {
                'symbol': 'GOOGL',
                'trend': 'bearish',
                'signals': {
                    'signal': 'sell',
                    'confidence': 0.65
                }
            }
        ]
        
        result = system._save_analysis_results(analysis_results)
        
        assert result == 2
    
    def test_save_analysis_results_exception(self, system):
        analysis_results = [{'invalid': 'data'}]
        
        result = system._save_analysis_results(analysis_results)
        
        assert result == 0
    
    @patch('time.sleep')
    def test_run_continuous_analysis(self, mock_sleep, system):
        system.run_analysis_cycle = Mock(return_value={'status': 'success', 'symbols_analyzed': 1})
        
        import signal
        import threading
        
        def stop_after_delay():
            import time
            time.sleep(0.1)
            raise KeyboardInterrupt()
        
        thread = threading.Thread(target=stop_after_delay)
        thread.daemon = True
        thread.start()
        
        try:
            system.run_continuous_analysis(interval_minutes=0.001)
        except KeyboardInterrupt:
            pass
        
        assert system.run_analysis_cycle.called
    
    @patch('time.sleep')
    def test_run_continuous_analysis_with_failure(self, mock_sleep, system):
        system.run_analysis_cycle = Mock(return_value={'status': 'failed', 'reason': 'error'})
        
        import signal
        import threading
        
        def stop_after_delay():
            import time
            time.sleep(0.1)
            raise KeyboardInterrupt()
        
        thread = threading.Thread(target=stop_after_delay)
        thread.daemon = True
        thread.start()
        
        try:
            system.run_continuous_analysis(interval_minutes=0.001)
        except KeyboardInterrupt:
            pass
        
        assert system.run_analysis_cycle.called
    
    @patch('time.sleep')
    def test_run_continuous_analysis_exception(self, mock_sleep, system):
        system.run_analysis_cycle = Mock(side_effect=Exception("Test error"))
        
        import signal
        import threading
        
        def stop_after_delay():
            import time
            time.sleep(0.1)
            raise KeyboardInterrupt()
        
        thread = threading.Thread(target=stop_after_delay)
        thread.daemon = True
        thread.start()
        
        try:
            system.run_continuous_analysis(interval_minutes=0.001)
        except KeyboardInterrupt:
            pass
        
        assert system.run_analysis_cycle.called

