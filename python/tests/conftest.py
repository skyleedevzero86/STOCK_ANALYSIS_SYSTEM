import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def sample_stock_data():
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    np.random.seed(42)
    
    return pd.DataFrame({
        'date': dates,
        'open': 100 + np.random.randn(len(dates)) * 0.5,
        'high': 105 + np.random.randn(len(dates)) * 0.5,
        'low': 95 + np.random.randn(len(dates)) * 0.5,
        'close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
        'volume': np.random.randint(1000000, 5000000, len(dates)),
        'symbol': 'AAPL'
    })

@pytest.fixture
def sample_realtime_data():
    return {
        'symbol': 'AAPL',
        'timestamp': datetime.now(),
        'price': 150.25,
        'volume': 1000000,
        'change': 2.5,
        'change_percent': 1.69,
        'market_cap': 2500000000000,
        'pe_ratio': 25.5,
        'high_52w': 180.0,
        'low_52w': 120.0
    }

@pytest.fixture
def sample_analysis_result():
    return {
        'symbol': 'AAPL',
        'current_price': 150.25,
        'trend': 'bullish',
        'trend_strength': 0.8,
        'signals': {
            'signal': 'buy',
            'confidence': 0.75,
            'signals': ['RSI 과매도 - 매수 신호', 'MACD 골든크로스 - 매수 신호'],
            'reason': '2개 매수 신호, 0개 매도 신호'
        },
        'anomalies': [
            {
                'type': 'volume_spike',
                'severity': 'high',
                'message': 'AAPL: 거래량 급증 (5,000,000 vs 평균 2,000,000)',
                'current_value': 5000000,
                'threshold': 4000000
            }
        ],
        'timestamp': datetime.now()
    }

@pytest.fixture
def sample_anomaly():
    return {
        'symbol': 'AAPL',
        'type': 'volume_spike',
        'severity': 'high',
        'message': 'AAPL: 거래량 급증 (5,000,000 vs 평균 2,000,000)',
        'current_value': 5000000,
        'threshold': 4000000
    }

@pytest.fixture
def sample_email_config():
    return {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'user': 'test@gmail.com',
        'password': 'test_password'
    }

@pytest.fixture
def sample_slack_webhook():
    return "https://hooks.slack.com/services/test/webhook"

@pytest.fixture
def sample_telegram_config():
    return {
        'bot_token': 'test_bot_token',
        'chat_id': 'test_chat_id'
    }

@pytest.fixture
def sample_notification_recipients():
    return ['analyst@company.com', 'trader@company.com']

@pytest.fixture
def sample_historical_chart_data():
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    np.random.seed(42)
    
    return [
        {
            'date': date.isoformat(),
            'close': 100 + np.random.randn() * 2,
            'volume': np.random.randint(1000000, 5000000),
            'rsi': 50 + np.random.randn() * 10,
            'macd': np.random.randn() * 0.5,
            'bb_upper': 105 + np.random.randn() * 2,
            'bb_lower': 95 + np.random.randn() * 2,
            'sma_20': 100 + np.random.randn() * 1
        }
        for date in dates
    ]

@pytest.fixture
def sample_websocket_message():
    return {
        'type': 'analysis_update',
        'data': [
            {
                'symbol': 'AAPL',
                'current_price': 150.25,
                'trend': 'bullish',
                'signals': {'signal': 'buy', 'confidence': 0.75},
                'timestamp': datetime.now().isoformat()
            }
        ]
    }

@pytest.fixture
def sample_error_response():
    return {
        'error': 'Data not found',
        'detail': 'The requested stock data could not be found'
    }

@pytest.fixture
def sample_api_health_response():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'uptime': '2 days, 5 hours'
    }

@pytest.fixture
def sample_symbols_list():
    return ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']

@pytest.fixture
def sample_quality_check_result():
    return {
        'symbol': 'AAPL',
        'is_valid': True,
        'missing_days': 0,
        'data_quality_score': 0.95,
        'issues': []
    }

@pytest.fixture
def sample_outlier_detection_result():
    return {
        'symbol': 'AAPL',
        'outliers': [
            {'date': '2024-01-15', 'close': 200.0, 'volume': 10000000}
        ],
        'outlier_count': 1,
        'outlier_percentage': 3.33
    }
