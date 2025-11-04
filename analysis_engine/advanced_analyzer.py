import pandas as pd
import numpy as np
import ta
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

class AdvancedTechnicalAnalyzer:
    
    def __init__(self):
        self.indicators = {}
        self.pattern_cache = {}
        self.ml_models = {}
        self.scaler = StandardScaler()
        
    def calculate_advanced_momentum_indicators(self, data: pd.DataFrame) -> Dict:
        if len(data) < 50:
            return {}
            
        indicators = {}
        
        indicators['rsi_14'] = ta.momentum.RSIIndicator(data['close'], window=14).rsi()
        indicators['rsi_21'] = ta.momentum.RSIIndicator(data['close'], window=21).rsi()
        indicators['stoch_k'] = ta.momentum.StochasticOscillator(data['high'], data['low'], data['close']).stoch()
        indicators['stoch_d'] = ta.momentum.StochasticOscillator(data['high'], data['low'], data['close']).stoch_signal()
        indicators['williams_r'] = ta.momentum.WilliamsRIndicator(data['high'], data['low'], data['close']).williams_r()
        indicators['roc'] = ta.momentum.ROCIndicator(data['close'], window=10).roc()
        indicators['ppo'] = ta.momentum.PercentagePriceOscillator(data['close']).ppo()
        indicators['ppo_signal'] = ta.momentum.PercentagePriceOscillator(data['close']).ppo_signal()
        indicators['ppo_histogram'] = ta.momentum.PercentagePriceOscillator(data['close']).ppo_hist()
        
        return indicators
    
    def calculate_advanced_trend_indicators(self, data: pd.DataFrame) -> Dict:
        if len(data) < 50:
            return {}
            
        indicators = {}
        
        indicators['ema_8'] = ta.trend.EMAIndicator(data['close'], window=8).ema_indicator()
        indicators['ema_21'] = ta.trend.EMAIndicator(data['close'], window=21).ema_indicator()
        indicators['ema_34'] = ta.trend.EMAIndicator(data['close'], window=34).ema_indicator()
        indicators['ema_55'] = ta.trend.EMAIndicator(data['close'], window=55).ema_indicator()
        indicators['ema_89'] = ta.trend.EMAIndicator(data['close'], window=89).ema_indicator()
        indicators['ema_144'] = ta.trend.EMAIndicator(data['close'], window=144).ema_indicator()
        indicators['ema_233'] = ta.trend.EMAIndicator(data['close'], window=233).ema_indicator()
        
        indicators['adx'] = ta.trend.ADXIndicator(data['high'], data['low'], data['close']).adx()
        indicators['adx_pos'] = ta.trend.ADXIndicator(data['high'], data['low'], data['close']).adx_pos()
        indicators['adx_neg'] = ta.trend.ADXIndicator(data['high'], data['low'], data['close']).adx_neg()
        
        indicators['aroon_up'] = ta.trend.AroonIndicator(data['close']).aroon_up()
        indicators['aroon_down'] = ta.trend.AroonIndicator(data['close']).aroon_down()
        indicators['aroon_indicator'] = ta.trend.AroonIndicator(data['close']).aroon_indicator()
        
        indicators['cci'] = ta.trend.CCIIndicator(data['high'], data['low'], data['close']).cci()
        indicators['dpo'] = ta.trend.DPOIndicator(data['close']).dpo()
        indicators['kst'] = ta.trend.KSTIndicator(data['close']).kst()
        indicators['kst_signal'] = ta.trend.KSTIndicator(data['close']).kst_sig()
        
        return indicators
    
    def calculate_advanced_volatility_indicators(self, data: pd.DataFrame) -> Dict:
        if len(data) < 50:
            return {}
            
        indicators = {}
        
        indicators['bb_upper'] = ta.volatility.BollingerBands(data['close']).bollinger_hband()
        indicators['bb_middle'] = ta.volatility.BollingerBands(data['close']).bollinger_mavg()
        indicators['bb_lower'] = ta.volatility.BollingerBands(data['close']).bollinger_lband()
        indicators['bb_width'] = ta.volatility.BollingerBands(data['close']).bollinger_wband()
        indicators['bb_percent'] = ta.volatility.BollingerBands(data['close']).bollinger_pband()
        
        indicators['atr'] = ta.volatility.AverageTrueRange(data['high'], data['low'], data['close']).average_true_range()
        indicators['natr'] = ta.volatility.AverageTrueRange(data['high'], data['low'], data['close']).average_true_range()
        indicators['trange'] = ta.volatility.AverageTrueRange(data['high'], data['low'], data['close']).true_range()
        
        indicators['kc_upper'] = ta.volatility.KeltnerChannel(data['high'], data['low'], data['close']).keltner_channel_hband()
        indicators['kc_middle'] = ta.volatility.KeltnerChannel(data['high'], data['low'], data['close']).keltner_channel_mband()
        indicators['kc_lower'] = ta.volatility.KeltnerChannel(data['high'], data['low'], data['close']).keltner_channel_lband()
        
        indicators['dc_upper'] = ta.volatility.DonchianChannel(data['high'], data['low'], data['close']).donchian_channel_hband()
        indicators['dc_middle'] = ta.volatility.DonchianChannel(data['high'], data['low'], data['close']).donchian_channel_mband()
        indicators['dc_lower'] = ta.volatility.DonchianChannel(data['high'], data['low'], data['close']).donchian_channel_lband()
        
        return indicators
    
    def calculate_advanced_volume_indicators(self, data: pd.DataFrame) -> Dict:
        if len(data) < 50 or 'volume' not in data.columns:
            return {}
            
        indicators = {}
        
        indicators['obv'] = ta.volume.OnBalanceVolumeIndicator(data['close'], data['volume']).on_balance_volume()
        indicators['ad'] = ta.volume.AccDistIndexIndicator(data['high'], data['low'], data['close'], data['volume']).acc_dist_index()
        indicators['cmf'] = ta.volume.ChaikinMoneyFlowIndicator(data['high'], data['low'], data['close'], data['volume']).chaikin_money_flow()
        indicators['fi'] = ta.volume.ForceIndexIndicator(data['close'], data['volume']).force_index()
        indicators['eom'] = ta.volume.EaseOfMovementIndicator(data['high'], data['low'], data['volume']).ease_of_movement()
        indicators['sma_eom'] = ta.volume.EaseOfMovementIndicator(data['high'], data['low'], data['volume']).sma_ease_of_movement()
        
        window = 20
        vwap = (data['close'] * data['volume']).rolling(window=window).sum() / data['volume'].rolling(window=window).sum()
        indicators['vwap'] = vwap
        indicators['vwma'] = vwap
        
        indicators['mfi'] = ta.volume.MFIIndicator(data['high'], data['low'], data['close'], data['volume']).money_flow_index()
        indicators['nvi'] = ta.volume.NegativeVolumeIndexIndicator(data['close'], data['volume']).negative_volume_index()
        indicators['pvi'] = ta.volume.PositiveVolumeIndexIndicator(data['close'], data['volume']).positive_volume_index()
        
        return indicators
    
    def detect_chart_patterns(self, data: pd.DataFrame) -> List[Dict]:
        if len(data) < 100:
            return []
            
        patterns = []
        
        head_and_shoulders = self._detect_head_and_shoulders(data)
        if head_and_shoulders:
            patterns.extend(head_and_shoulders)
            
        double_top_bottom = self._detect_double_top_bottom(data)
        if double_top_bottom:
            patterns.extend(double_top_bottom)
            
        triangle_patterns = self._detect_triangle_patterns(data)
        if triangle_patterns:
            patterns.extend(triangle_patterns)
            
        flag_patterns = self._detect_flag_patterns(data)
        if flag_patterns:
            patterns.extend(flag_patterns)
            
        return patterns
    
    def _detect_head_and_shoulders(self, data: pd.DataFrame) -> List[Dict]:
        if len(data) < 50:
            return []
            
        patterns = []
        highs = data['high'].values
        peaks, _ = find_peaks(highs, distance=5, prominence=np.std(highs) * 0.1)
        
        if len(peaks) >= 3:
            for i in range(len(peaks) - 2):
                left_shoulder = peaks[i]
                head = peaks[i + 1]
                right_shoulder = peaks[i + 2]
                
                if (highs[left_shoulder] < highs[head] and 
                    highs[right_shoulder] < highs[head] and
                    abs(highs[left_shoulder] - highs[right_shoulder]) / highs[head] < 0.05):
                    
                    patterns.append({
                        'type': 'head_and_shoulders',
                        'confidence': 0.8,
                        'left_shoulder': left_shoulder,
                        'head': head,
                        'right_shoulder': right_shoulder,
                        'signal': 'bearish'
                    })
        
        return patterns
    
    def _detect_double_top_bottom(self, data: pd.DataFrame) -> List[Dict]:
        if len(data) < 30:
            return []
            
        patterns = []
        highs = data['high'].values
        lows = data['low'].values
        
        peaks, _ = find_peaks(highs, distance=10, prominence=np.std(highs) * 0.1)
        troughs, _ = find_peaks(-lows, distance=10, prominence=np.std(lows) * 0.1)
        
        for i in range(len(peaks) - 1):
            if abs(highs[peaks[i]] - highs[peaks[i + 1]]) / highs[peaks[i]] < 0.02:
                patterns.append({
                    'type': 'double_top',
                    'confidence': 0.7,
                    'peak1': peaks[i],
                    'peak2': peaks[i + 1],
                    'signal': 'bearish'
                })
        
        for i in range(len(troughs) - 1):
            if abs(lows[troughs[i]] - lows[troughs[i + 1]]) / lows[troughs[i]] < 0.02:
                patterns.append({
                    'type': 'double_bottom',
                    'confidence': 0.7,
                    'trough1': troughs[i],
                    'trough2': troughs[i + 1],
                    'signal': 'bullish'
                })
        
        return patterns
    
    def _detect_triangle_patterns(self, data: pd.DataFrame) -> List[Dict]:
        if len(data) < 30:
            return []
            
        patterns = []
        highs = data['high'].values
        lows = data['low'].values
        
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        
        high_trend = np.polyfit(range(len(recent_highs)), recent_highs, 1)[0]
        low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)[0]
        
        if high_trend < 0 and low_trend > 0:
            patterns.append({
                'type': 'ascending_triangle',
                'confidence': 0.6,
                'signal': 'bullish'
            })
        elif high_trend > 0 and low_trend < 0:
            patterns.append({
                'type': 'descending_triangle',
                'confidence': 0.6,
                'signal': 'bearish'
            })
        elif abs(high_trend) < 0.001 and abs(low_trend) < 0.001:
            patterns.append({
                'type': 'symmetrical_triangle',
                'confidence': 0.5,
                'signal': 'neutral'
            })
        
        return patterns
    
    def _detect_flag_patterns(self, data: pd.DataFrame) -> List[Dict]:
        if len(data) < 20:
            return []
            
        patterns = []
        closes = data['close'].values
        
        recent_data = closes[-20:]
        volatility = np.std(recent_data)
        trend = np.polyfit(range(len(recent_data)), recent_data, 1)[0]
        
        if volatility < np.std(closes) * 0.5 and abs(trend) < np.std(closes) * 0.1:
            patterns.append({
                'type': 'flag',
                'confidence': 0.6,
                'signal': 'continuation'
            })
        
        return patterns
    
    def calculate_market_regime(self, data: pd.DataFrame) -> Dict:
        if len(data) < 50:
            return {'regime': 'unknown', 'confidence': 0}
            
        returns = data['close'].pct_change().dropna()
        volatility = returns.rolling(window=20).std()
        trend = data['close'].rolling(window=20).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        
        high_vol = volatility > volatility.quantile(0.8)
        strong_trend = abs(trend) > abs(trend).quantile(0.8)
        
        if high_vol.iloc[-1] and strong_trend.iloc[-1]:
            regime = 'trending_high_vol'
        elif high_vol.iloc[-1] and not strong_trend.iloc[-1]:
            regime = 'ranging_high_vol'
        elif not high_vol.iloc[-1] and strong_trend.iloc[-1]:
            regime = 'trending_low_vol'
        else:
            regime = 'ranging_low_vol'
        
        confidence = min(1.0, (abs(trend.iloc[-1]) + volatility.iloc[-1]) / 2)
        
        return {
            'regime': regime,
            'confidence': confidence,
            'volatility': volatility.iloc[-1],
            'trend_strength': abs(trend.iloc[-1])
        }
    
    def detect_anomalies_ml(self, data: pd.DataFrame) -> List[Dict]:
        if len(data) < 50:
            return []
            
        features = []
        for i in range(len(data)):
            if i < 20:
                continue
                
            recent_data = data.iloc[i-20:i+1]
            
            feature_vector = [
                recent_data['close'].pct_change().mean(),
                recent_data['close'].pct_change().std(),
                recent_data['volume'].mean() if 'volume' in recent_data.columns else 0,
                recent_data['volume'].std() if 'volume' in recent_data.columns else 0,
                (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
            ]
            features.append(feature_vector)
        
        if len(features) < 10:
            return []
            
        features_array = np.array(features)
        features_scaled = self.scaler.fit_transform(features_array)
        
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(features_scaled)
        
        anomalies = []
        for i, label in enumerate(anomaly_labels):
            if label == -1:
                anomalies.append({
                    'type': 'ml_anomaly',
                    'severity': 'high',
                    'index': i + 20,
                    'confidence': 0.8,
                    'features': features[i]
                })
        
        return anomalies
    
    def calculate_support_resistance(self, data: pd.DataFrame) -> Dict:
        if len(data) < 50:
            return {'support': [], 'resistance': []}
            
        highs = data['high'].values
        lows = data['low'].values
        
        high_peaks, _ = find_peaks(highs, distance=5, prominence=np.std(highs) * 0.1)
        low_troughs, _ = find_peaks(-lows, distance=5, prominence=np.std(lows) * 0.1)
        
        resistance_levels = []
        for peak in high_peaks:
            level = highs[peak]
            touches = np.sum(np.abs(highs - level) < level * 0.01)
            if touches >= 2:
                resistance_levels.append({
                    'level': level,
                    'touches': touches,
                    'strength': touches / len(highs) * 100
                })
        
        support_levels = []
        for trough in low_troughs:
            level = lows[trough]
            touches = np.sum(np.abs(lows - level) < level * 0.01)
            if touches >= 2:
                support_levels.append({
                    'level': level,
                    'touches': touches,
                    'strength': touches / len(lows) * 100
                })
        
        return {
            'support': sorted(support_levels, key=lambda x: x['strength'], reverse=True)[:5],
            'resistance': sorted(resistance_levels, key=lambda x: x['strength'], reverse=True)[:5]
        }
    
    def calculate_fibonacci_levels(self, data: pd.DataFrame) -> Dict:
        if len(data) < 50:
            return {}
            
        recent_data = data.tail(50)
        high = recent_data['high'].max()
        low = recent_data['low'].min()
        diff = high - low
        
        fibonacci_levels = {
            '0.0': high,
            '0.236': high - diff * 0.236,
            '0.382': high - diff * 0.382,
            '0.5': high - diff * 0.5,
            '0.618': high - diff * 0.618,
            '0.786': high - diff * 0.786,
            '1.0': low
        }
        
        current_price = data['close'].iloc[-1]
        nearest_level = min(fibonacci_levels.items(), key=lambda x: abs(x[1] - current_price))
        
        return {
            'levels': fibonacci_levels,
            'nearest_level': nearest_level[0],
            'distance_to_nearest': abs(nearest_level[1] - current_price) / current_price * 100
        }
    
    def calculate_advanced_signals(self, data: pd.DataFrame) -> Dict:
        if len(data) < 50:
            return {'signal': 'hold', 'confidence': 0, 'signals': []}
            
        signals = []
        confidence = 0
        
        momentum_indicators = self.calculate_advanced_momentum_indicators(data)
        trend_indicators = self.calculate_advanced_trend_indicators(data)
        volume_indicators = self.calculate_advanced_volume_indicators(data)
        
        if 'rsi_14' in momentum_indicators and not momentum_indicators['rsi_14'].isna().iloc[-1]:
            rsi = momentum_indicators['rsi_14'].iloc[-1]
            if rsi < 20:
                signals.append('RSI 극도 과매도')
                confidence += 0.3
            elif rsi > 80:
                signals.append('RSI 극도 과매수')
                confidence += 0.3
            elif 30 < rsi < 50:
                signals.append('RSI 상승 모멘텀')
                confidence += 0.2
            elif 50 < rsi < 70:
                signals.append('RSI 하락 모멘텀')
                confidence += 0.2
        
        if 'adx' in trend_indicators and not trend_indicators['adx'].isna().iloc[-1]:
            adx = trend_indicators['adx'].iloc[-1]
            if adx > 25:
                signals.append('강한 트렌드')
                confidence += 0.2
        
        if 'mfi' in volume_indicators and not volume_indicators['mfi'].isna().iloc[-1]:
            mfi = volume_indicators['mfi'].iloc[-1]
            if mfi < 20:
                signals.append('자금 유입 부족')
                confidence += 0.2
            elif mfi > 80:
                signals.append('자금 유입 과다')
                confidence += 0.2
        
        buy_signals = len([s for s in signals if '과매도' in s or '상승' in s or '유입' in s])
        sell_signals = len([s for s in signals if '과매수' in s or '하락' in s or '부족' in s])
        
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
            'momentum_score': buy_signals - sell_signals
        }
    
    def calculate_all_advanced_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty or len(data) < 50:
            return data
        
        momentum = self.calculate_advanced_momentum_indicators(data)
        trend = self.calculate_advanced_trend_indicators(data)
        volatility = self.calculate_advanced_volatility_indicators(data)
        volume = self.calculate_advanced_volume_indicators(data)
        
        for key, value in momentum.items():
            data[key] = value
        
        for key, value in trend.items():
            data[key] = value
        
        for key, value in volatility.items():
            data[key] = value
        
        for key, value in volume.items():
            data[key] = value
        
        return data
