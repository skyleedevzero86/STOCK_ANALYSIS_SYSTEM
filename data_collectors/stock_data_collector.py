import yfinance as yf
import pandas as pd
import requests
import time
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import json
from config.settings import settings

class StockDataCollector:
    
    def __init__(self, symbols: List[str], use_mock_data: bool = False, use_alpha_vantage: bool = True, fallback_to_mock: bool = True):
        self.symbols = symbols
        self.session = requests.Session()
        self.use_mock_data = use_mock_data
        self.use_alpha_vantage = use_alpha_vantage
        self.fallback_to_mock = fallback_to_mock
        self.alpha_vantage_api_key = settings.ALPHA_VANTAGE_API_KEY
        self.mock_data_cache = {}
        self.alpha_vantage_cache = {}
        self.rate_limit_delay = 12
        
    def get_historical_data(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        if self.use_mock_data:
            return self._generate_mock_historical_data(symbol, period)
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                return self._generate_mock_historical_data(symbol, period)
                
            data.reset_index(inplace=True)
            data.columns = [col.lower().replace(' ', '_') for col in data.columns]
            
            data['symbol'] = symbol
            
            return data
            
        except Exception as e:
            return self._generate_mock_historical_data(symbol, period)
    
    def get_realtime_data(self, symbol: str) -> Dict:
        if self.use_mock_data:
            logging.warning(f"Mock 데이터 모드: {symbol}에 대한 모의 데이터를 반환합니다.")
            return self._generate_mock_realtime_data(symbol)
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'currentPrice' not in info:
                raise ValueError(f"Yahoo Finance에서 {symbol} 정보를 가져올 수 없습니다.")
            
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                latest_price = float(hist['Close'].iloc[-1])
                volume = int(hist['Volume'].iloc[-1])
            else:
                latest_price = float(info.get('currentPrice', 0))
                volume = int(info.get('volume', 0))
            
            if latest_price <= 0:
                raise ValueError(f"Yahoo Finance에서 {symbol}의 가격이 0입니다.")
            
            change = float(info.get('regularMarketChange', 0))
            change_percent = float(info.get('regularMarketChangePercent', 0))
            
            realtime_data = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price': latest_price,
                'volume': volume,
                'change': change,
                'change_percent': change_percent,
                'market_cap': int(info.get('marketCap', 0)),
                'pe_ratio': float(info.get('trailingPE', 0)),
                'high_52w': float(info.get('fiftyTwoWeekHigh', 0)),
                'low_52w': float(info.get('fiftyTwoWeekLow', 0)),
                'confidence_score': 0.95
            }
            
            logging.info(f"Yahoo Finance에서 {symbol} 데이터 수집 성공: ${latest_price:.2f}")
            return realtime_data
            
        except Exception as e:
            logging.warning(f"Yahoo Finance에서 {symbol} 데이터 수집 실패: {str(e)}")
            
            if self.use_alpha_vantage:
                try:
                    logging.info(f"Alpha Vantage로 {symbol} 데이터 수집 시도...")
                    alpha_data = self.get_alpha_vantage_global_quote(symbol)
                    
                    if alpha_data and alpha_data.get('price', 0) > 0:
                        realtime_data = {
                            'symbol': symbol,
                            'timestamp': datetime.now(),
                            'price': float(alpha_data['price']),
                            'volume': int(alpha_data.get('volume', 0)),
                            'change': float(alpha_data.get('change', 0)),
                            'change_percent': float(alpha_data.get('change_percent', 0)),
                            'market_cap': 0,
                            'pe_ratio': 0,
                            'high_52w': float(alpha_data.get('high', 0)),
                            'low_52w': float(alpha_data.get('low', 0)),
                            'confidence_score': 0.85
                        }
                        logging.info(f"Alpha Vantage에서 {symbol} 데이터 수집 성공: ${alpha_data['price']:.2f}")
                        return realtime_data
                    else:
                        logging.warning(f"Alpha Vantage에서 {symbol} 데이터를 가져올 수 없습니다.")
                except Exception as alpha_e:
                    logging.error(f"Alpha Vantage에서 {symbol} 데이터 수집 실패: {str(alpha_e)}")
            
            if self.fallback_to_mock:
                logging.warning(f"모든 데이터 소스 실패, {symbol}에 대한 모의 데이터를 반환합니다.")
                return self._generate_mock_realtime_data(symbol)
            else:
                logging.error(f"{symbol}에 대한 실제 데이터를 가져올 수 없습니다.")
                return {
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'price': 0.0,
                    'volume': 0,
                    'change': 0.0,
                    'change_percent': 0.0,
                    'market_cap': 0,
                    'pe_ratio': 0,
                    'high_52w': 0,
                    'low_52w': 0,
                    'confidence_score': 0.0
                }
    
    def get_multiple_realtime_data(self) -> List[Dict]:
        results = []
        
        for symbol in self.symbols:
            data = self.get_realtime_data(symbol)
            if data:
                results.append(data)
            time.sleep(0.1)
            
        return results
    
    def get_alpha_vantage_global_quote(self, symbol: str) -> Dict:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                return {}
            
            if 'Note' in data:
                return {}
            
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                if not quote.get('05. price') or quote.get('05. price') == '0.0000':
                    return {}
                
                return {
                    'symbol': symbol,
                    'price': float(quote.get('05. price', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': float(quote.get('10. change percent', '0%').replace('%', '')),
                    'volume': int(quote.get('06. volume', 0)),
                    'high': float(quote.get('03. high', 0)),
                    'low': float(quote.get('04. low', 0)),
                    'open': float(quote.get('02. open', 0)),
                    'previous_close': float(quote.get('08. previous close', 0)),
                    'timestamp': datetime.now()
                }
            else:
                return {}
            
        except requests.exceptions.Timeout:
            return {}
        except requests.exceptions.RequestException as e:
            return {}
        except (ValueError, KeyError) as e:
            return {}
        except Exception as e:
            return {}
    
    def get_alpha_vantage_daily_data(self, symbol: str, outputsize: str = "compact") -> pd.DataFrame:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'outputsize': outputsize,
                'apikey': self.alpha_vantage_api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                df_data = []
                
                for date, values in time_series.items():
                    df_data.append({
                        'date': pd.to_datetime(date),
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['5. volume']),
                        'symbol': symbol
                    })
                
                df = pd.DataFrame(df_data)
                df = df.sort_values('date').reset_index(drop=True)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            return pd.DataFrame()
    
    def get_alpha_vantage_intraday_data(self, symbol: str, interval: str = "5min", outputsize: str = "compact") -> pd.DataFrame:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.alpha_vantage_api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if f'Time Series ({interval})' in data:
                time_series = data[f'Time Series ({interval})']
                df_data = []
                
                for datetime_str, values in time_series.items():
                    df_data.append({
                        'datetime': pd.to_datetime(datetime_str),
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['5. volume']),
                        'symbol': symbol
                    })
                
                df = pd.DataFrame(df_data)
                df = df.sort_values('datetime').reset_index(drop=True)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            return pd.DataFrame()
    
    def get_alpha_vantage_weekly_data(self, symbol: str) -> pd.DataFrame:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_WEEKLY',
                'symbol': symbol,
                'apikey': self.alpha_vantage_api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'Weekly Time Series' in data:
                time_series = data['Weekly Time Series']
                df_data = []
                
                for date, values in time_series.items():
                    df_data.append({
                        'date': pd.to_datetime(date),
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['5. volume']),
                        'symbol': symbol
                    })
                
                df = pd.DataFrame(df_data)
                df = df.sort_values('date').reset_index(drop=True)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            return pd.DataFrame()
    
    def get_alpha_vantage_monthly_data(self, symbol: str) -> pd.DataFrame:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_MONTHLY',
                'symbol': symbol,
                'apikey': self.alpha_vantage_api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'Monthly Time Series' in data:
                time_series = data['Monthly Time Series']
                df_data = []
                
                for date, values in time_series.items():
                    df_data.append({
                        'date': pd.to_datetime(date),
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['5. volume']),
                        'symbol': symbol
                    })
                
                df = pd.DataFrame(df_data)
                df = df.sort_values('date').reset_index(drop=True)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            return pd.DataFrame()
    
    def search_alpha_vantage_symbols(self, keywords: str) -> List[Dict]:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': keywords,
                'apikey': self.alpha_vantage_api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'bestMatches' in data:
                matches = []
                for match in data['bestMatches']:
                    matches.append({
                        'symbol': match['1. symbol'],
                        'name': match['2. name'],
                        'type': match['3. type'],
                        'region': match['4. region'],
                        'market_open': match['5. marketOpen'],
                        'market_close': match['6. marketClose'],
                        'timezone': match['7. timezone'],
                        'currency': match['8. currency'],
                        'match_score': float(match['9. matchScore'])
                    })
                return matches
            else:
                return []
                
        except Exception as e:
            return []
    
    def collect_batch_data(self) -> Dict[str, pd.DataFrame]:
        all_data = {}
        
        for symbol in self.symbols:
            data = self.get_historical_data(symbol, period="3mo")
            
            if not data.empty:
                all_data[symbol] = data
                
            time.sleep(1)
            
        return all_data
    
    def _generate_mock_realtime_data(self, symbol: str) -> Dict:
        if symbol in self.mock_data_cache:
            base_data = self.mock_data_cache[symbol]
            price_change = np.random.normal(0, 0.02)
            new_price = base_data['price'] * (1 + price_change)
            new_change_percent = base_data['change_percent'] + np.random.normal(0, 0.5)
        else:
            base_price = 100 + hash(symbol) % 200
            price_change = np.random.normal(0, 0.02)
            new_price = base_price * (1 + price_change)
            new_change_percent = np.random.normal(0, 2)
        
        mock_data = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'price': float(new_price),
            'volume': int(np.random.randint(1000000, 5000000)),
            'change': float(new_price * new_change_percent / 100),
            'change_percent': float(new_change_percent),
            'market_cap': int(new_price * np.random.randint(1000000000, 2000000000)),
            'pe_ratio': float(np.random.uniform(15, 35)),
            'high_52w': float(new_price * np.random.uniform(1.1, 1.5)),
            'low_52w': float(new_price * np.random.uniform(0.5, 0.9))
        }
        
        self.mock_data_cache[symbol] = mock_data
        return mock_data
    
    def _generate_mock_historical_data(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        days = 30 if period == "1mo" else 90 if period == "3mo" else 7
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        np.random.seed(hash(symbol) % 2**32)
        
        base_price = 100 + hash(symbol) % 200
        
        price_changes = np.random.randn(len(dates)) * 0.02
        prices = base_price * np.exp(np.cumsum(price_changes))
        
        opens = prices * (1 + np.random.normal(0, 0.01, len(dates)))
        highs = np.maximum(opens, prices) * (1 + np.random.uniform(0, 0.02, len(dates)))
        lows = np.minimum(opens, prices) * (1 - np.random.uniform(0, 0.02, len(dates)))
        closes = prices
        
        volumes = np.random.randint(1000000, 5000000, len(dates))
        
        mock_data = pd.DataFrame({
            'date': dates,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes,
            'symbol': symbol
        })
        
        return mock_data

class DataQualityChecker:
    
    @staticmethod
    def check_data_completeness(data: pd.DataFrame, symbol: str) -> Dict:
        if data.empty:
            return {
                'symbol': symbol,
                'is_valid': False,
                'missing_days': 0,
                'data_quality_score': 0.0,
                'issues': ['데이터 없음']
            }
        
        expected_days = 30
        actual_days = len(data)
        missing_days = max(0, expected_days - actual_days)
        
        quality_score = max(0.0, (actual_days / expected_days))
        
        issues = []
        if missing_days > 0:
            issues.append(f"{missing_days}일 데이터 누락")
        
        if 'close' in data.columns:
            zero_prices = (data['close'] <= 0).sum()
            if zero_prices > 0:
                issues.append(f"{zero_prices}개 0 또는 음수 가격")
                quality_score *= 0.8
        
        return {
            'symbol': symbol,
            'is_valid': quality_score > 0.7,
            'missing_days': missing_days,
            'data_quality_score': quality_score,
            'issues': issues
        }
    
    @staticmethod
    def detect_outliers(data: pd.DataFrame, symbol: str) -> Dict:
        if data.empty or 'close' not in data.columns:
            return {'symbol': symbol, 'outliers': [], 'outlier_count': 0}
        
        prices = data['close']
        
        Q1 = prices.quantile(0.25)
        Q3 = prices.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = data[(prices < lower_bound) | (prices > upper_bound)]
        
        return {
            'symbol': symbol,
            'outliers': outliers.to_dict('records') if not outliers.empty else [],
            'outlier_count': len(outliers),
            'outlier_percentage': len(outliers) / len(data) * 100
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    collector = StockDataCollector(symbols)
    
    print("=== 실시간 데이터 수집 테스트 ===")
    realtime_data = collector.get_multiple_realtime_data()
    for data in realtime_data:
        print(f"{data['symbol']}: ${data['price']:.2f} ({data['change_percent']:.2f}%)")
    
    print("\n=== 과거 데이터 수집 테스트 ===")
    historical_data = collector.collect_batch_data()
    for symbol, data in historical_data.items():
        print(f"{symbol}: {len(data)}일 데이터")
    
    print("\n=== 데이터 품질 검사 ===")
    checker = DataQualityChecker()
    for symbol, data in historical_data.items():
        quality = checker.check_data_completeness(data, symbol)
        print(f"{symbol}: 품질점수 {quality['data_quality_score']:.2f}")