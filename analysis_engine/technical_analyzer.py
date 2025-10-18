import pandas as pd
import numpy as np
import ta
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta

class TechnicalAnalyzer:
    
    def __init__(self):
        self.indicators = {}
        
    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        return ta.momentum.RSIIndicator(data['close'], window=period).rsi()
    
    def calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        macd_indicator = ta.trend.MACD(data['close'], window_fast=fast, window_slow=slow, window_sign=signal)
        
        return {
            'macd': macd_indicator.macd(),
            'macd_signal': macd_indicator.macd_signal(),
            'macd_histogram': macd_indicator.macd_diff()
        }
    
    def calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, std: float = 2) -> Dict:
        bb_indicator = ta.volatility.BollingerBands(data['close'], window=period, window_dev=std)
        
        return {
            'bb_upper': bb_indicator.bollinger_hband(),
            'bb_middle': bb_indicator.bollinger_mavg(),
            'bb_lower': bb_indicator.bollinger_lband()
        }
    
    def calculate_moving_averages(self, data: pd.DataFrame) -> Dict:
        return {
            'sma_20': ta.trend.SMAIndicator(data['close'], window=20).sma_indicator(),
            'sma_50': ta.trend.SMAIndicator(data['close'], window=50).sma_indicator(),
            'ema_12': ta.trend.EMAIndicator(data['close'], window=12).ema_indicator(),
            'ema_26': ta.trend.EMAIndicator(data['close'], window=26).ema_indicator()
        }
    
    def calculate_volume_indicators(self, data: pd.DataFrame) -> Dict:
        return {
            'volume_sma': ta.volume.VolumeSMAIndicator(data['close'], data['volume'], window=20).volume_sma(),
            'volume_ema': ta.volume.VolumeEMAIndicator(data['close'], data['volume'], window=20).volume_ema(),
            'obv': ta.volume.OnBalanceVolumeIndicator(data['close'], data['volume']).on_balance_volume()
        }
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty or len(data) < 50:
            logging.warning("데이터가 부족합니다 (최소 50일 필요)")
            return data
        
        data['rsi_14'] = self.calculate_rsi(data)
        
        macd_data = self.calculate_macd(data)
        data['macd'] = macd_data['macd']
        data['macd_signal'] = macd_data['macd_signal']
        data['macd_histogram'] = macd_data['macd_histogram']
        
        bb_data = self.calculate_bollinger_bands(data)
        data['bb_upper'] = bb_data['bb_upper']
        data['bb_middle'] = bb_data['bb_middle']
        data['bb_lower'] = bb_data['bb_lower']
        
        ma_data = self.calculate_moving_averages(data)
        data['sma_20'] = ma_data['sma_20']
        data['sma_50'] = ma_data['sma_50']
        data['ema_12'] = ma_data['ema_12']
        data['ema_26'] = ma_data['ema_26']
        
        if 'volume' in data.columns:
            volume_data = self.calculate_volume_indicators(data)
            data['volume_sma'] = volume_data['volume_sma']
            data['volume_ema'] = volume_data['volume_ema']
            data['obv'] = volume_data['obv']
        
        return data
    
    def analyze_trend(self, data: pd.DataFrame) -> Dict:
        if data.empty:
            return {'trend': 'unknown', 'strength': 0, 'signals': []}
        
        latest = data.iloc[-1]
        signals = []
        
        if 'sma_20' in data.columns and 'sma_50' in data.columns:
            if latest['sma_20'] > latest['sma_50']:
                signals.append('상승 추세 (SMA20 > SMA50)')
            else:
                signals.append('하락 추세 (SMA20 < SMA50)')
        
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            if latest['macd'] > latest['macd_signal']:
                signals.append('MACD 상승 신호')
            else:
                signals.append('MACD 하락 신호')
        
        if 'rsi_14' in data.columns:
            rsi = latest['rsi_14']
            if rsi > 70:
                signals.append('RSI 과매수 (70 이상)')
            elif rsi < 30:
                signals.append('RSI 과매도 (30 이하)')
            elif rsi > 50:
                signals.append('RSI 상승 모멘텀')
            else:
                signals.append('RSI 하락 모멘텀')
        
        bullish_signals = len([s for s in signals if '상승' in s or '과매도' in s])
        bearish_signals = len([s for s in signals if '하락' in s or '과매수' in s])
        
        if bullish_signals > bearish_signals:
            trend = 'bullish'
            strength = bullish_signals / len(signals) if signals else 0
        elif bearish_signals > bullish_signals:
            trend = 'bearish'
            strength = bearish_signals / len(signals) if signals else 0
        else:
            trend = 'neutral'
            strength = 0.5
        
        return {
            'trend': trend,
            'strength': strength,
            'signals': signals
        }
    
    def detect_anomalies(self, data: pd.DataFrame, symbol: str) -> List[Dict]:
        anomalies = []
        
        if data.empty or len(data) < 20:
            return anomalies
        
        latest = data.iloc[-1]
        recent_data = data.tail(20)
        
        if 'volume' in data.columns:
            avg_volume = recent_data['volume'].mean()
            current_volume = latest['volume']
            
            if current_volume > avg_volume * 2.0:
                anomalies.append({
                    'type': 'volume_spike',
                    'severity': 'high',
                    'message': f'{symbol}: 거래량 급증 ({current_volume:,.0f} vs 평균 {avg_volume:,.0f})',
                    'current_value': current_volume,
                    'threshold': avg_volume * 2.0
                })
        
        if 'close' in data.columns:
            price_change = (latest['close'] - data.iloc[-2]['close']) / data.iloc[-2]['close'] * 100
            
            if abs(price_change) > 5.0:
                anomalies.append({
                    'type': 'price_spike',
                    'severity': 'high' if abs(price_change) > 10 else 'medium',
                    'message': f'{symbol}: 가격 급변동 ({price_change:+.2f}%)',
                    'current_value': price_change,
                    'threshold': 5.0
                })
        
        if 'rsi_14' in data.columns:
            rsi = latest['rsi_14']
            if rsi > 80:
                anomalies.append({
                    'type': 'rsi_extreme',
                    'severity': 'high',
                    'message': f'{symbol}: RSI 극도 과매수 ({rsi:.1f})',
                    'current_value': rsi,
                    'threshold': 80
                })
            elif rsi < 20:
                anomalies.append({
                    'type': 'rsi_extreme',
                    'severity': 'high',
                    'message': f'{symbol}: RSI 극도 과매도 ({rsi:.1f})',
                    'current_value': rsi,
                    'threshold': 20
                })
        
        return anomalies
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> Dict:
        if data.empty or len(data) < 20:
            return {'signal': 'hold', 'confidence': 0, 'reason': '데이터 부족'}
        
        latest = data.iloc[-1]
        signals = []
        confidence = 0
        
        if 'rsi_14' in data.columns:
            rsi = latest['rsi_14']
            if rsi < 30:
                signals.append('RSI 과매도 - 매수 신호')
                confidence += 0.3
            elif rsi > 70:
                signals.append('RSI 과매수 - 매도 신호')
                confidence += 0.3
        
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            macd = latest['macd']
            macd_signal = latest['macd_signal']
            macd_hist = latest.get('macd_histogram', 0)
            
            if macd > macd_signal and macd_hist > 0:
                signals.append('MACD 골든크로스 - 매수 신호')
                confidence += 0.4
            elif macd < macd_signal and macd_hist < 0:
                signals.append('MACD 데드크로스 - 매도 신호')
                confidence += 0.4
        
        if all(col in data.columns for col in ['close', 'bb_upper', 'bb_lower']):
            close = latest['close']
            bb_upper = latest['bb_upper']
            bb_lower = latest['bb_lower']
            
            if close <= bb_lower:
                signals.append('볼린저 밴드 하단 터치 - 매수 신호')
                confidence += 0.2
            elif close >= bb_upper:
                signals.append('볼린저 밴드 상단 터치 - 매도 신호')
                confidence += 0.2
        
        buy_signals = len([s for s in signals if '매수' in s])
        sell_signals = len([s for s in signals if '매도' in s])
        
        if buy_signals > sell_signals:
            signal = 'buy'
        elif sell_signals > buy_signals:
            signal = 'sell'
        else:
            signal = 'hold'
        
        return {
            'signal': signal,
            'confidence': min(confidence, 1.0),
            'signals': signals,
            'reason': f"{buy_signals}개 매수 신호, {sell_signals}개 매도 신호"
        }

if __name__ == "__main__":
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)
    
    sample_data = pd.DataFrame({
        'date': dates,
        'close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
        'volume': np.random.randint(1000000, 5000000, len(dates))
    })
    
    analyzer = TechnicalAnalyzer()
    
    analyzed_data = analyzer.calculate_all_indicators(sample_data)
    print(f"계산된 지표 수: {len([col for col in analyzed_data.columns if col not in ['date', 'close', 'volume']])}")
    
    trend_analysis = analyzer.analyze_trend(analyzed_data)
    print(f"트렌드: {trend_analysis['trend']} (강도: {trend_analysis['strength']:.2f})")
    for signal in trend_analysis['signals']:
        print(f"  - {signal}")
    
    anomalies = analyzer.detect_anomalies(analyzed_data, 'TEST')
    for anomaly in anomalies:
        print(f"  - {anomaly['message']}")
    
    signals = analyzer.generate_signals(analyzed_data, 'TEST')
    print(f"신호: {signals['signal']} (신뢰도: {signals['confidence']:.2f})")
    print(f"이유: {signals['reason']}")
