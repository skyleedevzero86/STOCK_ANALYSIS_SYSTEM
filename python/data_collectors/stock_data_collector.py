import yfinance as yf
import pandas as pd
import requests
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import json
from config.settings import settings
from config.logging_config import get_logger
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = get_logger(__name__)
from exceptions import (
    StockDataCollectionError,
    StockNotFoundError,
    InvalidSymbolError,
    DataSourceUnavailableError,
    TimeoutError,
    ConnectionError,
    NetworkError,
    RateLimitError,
    HTTPError,
    YahooFinanceError,
    AlphaVantageError,
    ExternalServiceError
)

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
        self.rate_limit_delay = 3.0 
        self.last_request_time = {}  
        self.rate_limit_backoff = {} 
        self.min_delay_between_requests = 2.0  
        
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
            
        except (StockDataCollectionError, StockNotFoundError, InvalidSymbolError) as e:
            logger.warning("과거 데이터 수집 실패, 모의 데이터 사용", symbol=symbol, exception=e)
            return self._generate_mock_historical_data(symbol, period)
        except (TimeoutError, ConnectionError, NetworkError) as e:
            logger.warning("과거 데이터 수집 네트워크 오류, 모의 데이터 사용", symbol=symbol, exception=e)
            return self._generate_mock_historical_data(symbol, period)
        except Exception as e:
            logger.warning("과거 데이터 수집 예상치 못한 오류, 모의 데이터 사용", symbol=symbol, exception=e)
            return self._generate_mock_historical_data(symbol, period)
    
    def _wait_if_needed(self, source_name: str):
        current_time = time.time()
        last_time = self.last_request_time.get(source_name, 0)
        backoff_time = self.rate_limit_backoff.get(source_name, 0)
        
        if backoff_time > current_time:
            wait_time = backoff_time - current_time
            logger.info(f"{source_name} 백오프 대기: {wait_time:.1f}초", component="StockDataCollector")
            time.sleep(wait_time)
            self.rate_limit_backoff[source_name] = 0
        
        elapsed = current_time - last_time
        if elapsed < self.min_delay_between_requests:
            wait_time = self.min_delay_between_requests - elapsed
            time.sleep(wait_time)
        
        self.last_request_time[source_name] = time.time()
    
    def get_realtime_data(self, symbol: str) -> Dict:
        if self.use_mock_data:
            logger.warning("Mock 데이터 모드: 모의 데이터를 반환합니다", symbol=symbol, component="StockDataCollector")
            return self._generate_mock_realtime_data(symbol)
        
        data_sources = [
            ('yfinance', self._fetch_yfinance_data),
            ('alpha_vantage', self._fetch_alpha_vantage_fallback),
            ('yahoo_direct', self._fetch_yahoo_direct_api)
        ]
        
        last_exception = None
        
        for source_name, fetch_func in data_sources:
            try:
                if source_name == 'alpha_vantage' and not self.use_alpha_vantage:
                    continue
                
                self._wait_if_needed(source_name)
                
                logger.info("데이터 수집 시도", symbol=symbol, source=source_name, component="StockDataCollector")
                result = fetch_func(symbol)
                
                if result and result.get('price', 0) > 0:
                    logger.info("데이터 수집 성공", symbol=symbol, source=source_name, price=result['price'], component="StockDataCollector")
                    if source_name in self.rate_limit_backoff:
                        self.rate_limit_backoff[source_name] = 0
                    return result
                else:
                    raise StockDataCollectionError(
                        f"{source_name} returned invalid data for {symbol}",
                        error_code="INVALID_DATA",
                        cause=None
                    )
                    
            except (StockDataCollectionError, StockNotFoundError, InvalidSymbolError) as e:
                last_exception = e
                logger.warning("데이터 수집 실패", symbol=symbol, source=source_name, exception=e)
                time.sleep(0.5)
                continue
            except (TimeoutError, ConnectionError, NetworkError, RateLimitError) as e:
                last_exception = e
                logger.warning("데이터 수집 네트워크 오류", symbol=symbol, source=source_name, exception=e)
                if isinstance(e, RateLimitError) and hasattr(e, 'retry_after'):
                    backoff_until = time.time() + e.retry_after
                    self.rate_limit_backoff[source_name] = backoff_until
                    logger.warning(f"{source_name} 레이트 리밋으로 인해 {e.retry_after}초 대기", symbol=symbol, component="StockDataCollector")
                time.sleep(1.0)
                continue
            except (YahooFinanceError, AlphaVantageError, ExternalServiceError) as e:
                last_exception = e
                logger.warning("데이터 수집 외부 서비스 오류", symbol=symbol, source=source_name, exception=e)
                time.sleep(0.5)
                continue
            except Exception as e:
                last_exception = e
                error_str = str(e)
                if '429' in error_str or 'Too Many Requests' in error_str:
                    current_backoff = self.rate_limit_backoff.get(source_name, 0)
                    if current_backoff <= time.time():
                        backoff_duration = 60
                    else:
                        backoff_duration = 120
                    backoff_until = time.time() + backoff_duration
                    self.rate_limit_backoff[source_name] = backoff_until
                    logger.warning(f"{source_name} 429 에러로 인해 {backoff_duration}초 백오프", symbol=symbol, component="StockDataCollector")
                    time.sleep(2.0)
                else:
                    logger.warning("데이터 수집 예상치 못한 오류", symbol=symbol, source=source_name, exception=e)
                time.sleep(0.5)
                continue
        
        if self.fallback_to_mock:
            logger.warning("모든 데이터 소스 실패, 모의 데이터를 반환합니다", symbol=symbol, component="StockDataCollector")
            return self._generate_mock_realtime_data(symbol)
        else:
            logger.error("실제 데이터를 가져올 수 없습니다", symbol=symbol, component="StockDataCollector")
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
    
    def _fetch_yfinance_data(self, symbol: str) -> Dict:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'currentPrice' not in info:
                raise YahooFinanceError(
                    f"Yahoo Finance에서 {symbol} 정보를 가져올 수 없습니다.",
                    service_name="Yahoo Finance",
                    cause=None
                )
        except (YahooFinanceError, RateLimitError):
            raise
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'Too Many Requests' in error_str:
                raise RateLimitError(
                    f"Yahoo Finance API rate limit exceeded for {symbol}",
                    service_name="Yahoo Finance",
                    retry_after=60
                )
            raise YahooFinanceError(
                f"Yahoo Finance에서 {symbol} 정보를 가져오는 중 오류 발생: {error_str}",
                service_name="Yahoo Finance",
                cause=e
            )
        
        if not info or 'currentPrice' not in info:
            raise YahooFinanceError(
                f"Yahoo Finance에서 {symbol} 정보를 가져올 수 없습니다.",
                service_name="Yahoo Finance",
                cause=None
            )
        
        hist = ticker.history(period="1d", interval="1m")
        if not hist.empty:
            latest_price = float(hist['Close'].iloc[-1])
            volume = int(hist['Volume'].iloc[-1])
        else:
            latest_price = float(info.get('currentPrice', 0))
            volume = int(info.get('volume', 0))
        
        if latest_price <= 0:
            raise YahooFinanceError(
                f"Yahoo Finance에서 {symbol}의 가격이 0입니다.",
                service_name="Yahoo Finance",
                cause=None
            )
        
        change = float(info.get('regularMarketChange', 0))
        change_percent = float(info.get('regularMarketChangePercent', 0))
        
        return {
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
    
    def _fetch_alpha_vantage_fallback(self, symbol: str) -> Dict:
        alpha_data = self.get_alpha_vantage_global_quote(symbol)
        
        if alpha_data and alpha_data.get('price', 0) > 0:
            return {
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
        else:
            raise AlphaVantageError(
                "Alpha Vantage returned empty or invalid data",
                service_name="Alpha Vantage",
                cause=None
            )
    
    def _fetch_yahoo_direct_api(self, symbol: str) -> Dict:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            'range': '1d',
            'interval': '1m',
            'includePrePost': 'true',
            'useYfid': 'true',
            'corsDomain': 'finance.yahoo.com'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = self.session.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 429:
            retry_after = 60
            if 'Retry-After' in response.headers:
                try:
                    retry_after = int(response.headers['Retry-After'])
                except ValueError:
                    retry_after = 60
            
            logger.warning(f"Yahoo Finance rate limit (429), {retry_after}초 대기 필요", symbol=symbol, component="StockDataCollector")
            raise RateLimitError(
                f"Yahoo Finance API rate limit exceeded for {symbol}",
                service_name="Yahoo Finance",
                retry_after=retry_after
            )
        
        response.raise_for_status()
        data = response.json()
        
        if 'chart' not in data or not data['chart']['result']:
            raise ValueError("Invalid Yahoo Finance API response")
        
        result = data['chart']['result'][0]
        meta = result.get('meta', {})
        timestamps = result.get('timestamp', [])
        indicators = result.get('indicators', {})
        
        if not timestamps or 'quote' not in indicators:
            raise YahooFinanceError(
                "Missing required data in Yahoo Finance API response",
                service_name="Yahoo Finance",
                cause=None
            )
        
        quote = indicators['quote'][0]
        latest_idx = -1
        
        price = quote.get('close', [0])[latest_idx] or meta.get('regularMarketPrice', 0)
        volume = quote.get('volume', [0])[latest_idx] or meta.get('regularMarketVolume', 0)
        change = meta.get('regularMarketChange', 0)
        change_percent = meta.get('regularMarketChangePercent', 0)
        
        if price <= 0:
            raise YahooFinanceError(
                f"Invalid price from Yahoo Direct API: {price}",
                service_name="Yahoo Finance",
                cause=None
            )
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'price': float(price),
            'volume': int(volume),
            'change': float(change),
            'change_percent': float(change_percent),
            'market_cap': meta.get('marketCap', 0),
            'pe_ratio': meta.get('trailingPE', 0),
            'high_52w': meta.get('fiftyTwoWeekHigh', 0),
            'low_52w': meta.get('fiftyTwoWeekLow', 0),
            'confidence_score': 0.90
        }
    
    def get_multiple_realtime_data(self) -> List[Dict]:
        results = []
        
        for idx, symbol in enumerate(self.symbols):
            data = self.get_realtime_data(symbol)
            if data:
                results.append(data)
            
            if idx < len(self.symbols) - 1:
                time.sleep(self.rate_limit_delay)
            
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
            
        except requests.exceptions.Timeout as e:
            logger.warning("Alpha Vantage 타임아웃", symbol=symbol, exception=e, component="StockDataCollector")
            return {}
        except requests.exceptions.ConnectionError as e:
            logger.warning("Alpha Vantage 연결 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return {}
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                logger.warning("Alpha Vantage 레이트 리밋", symbol=symbol, component="StockDataCollector")
            else:
                logger.warning("Alpha Vantage HTTP 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return {}
        except requests.exceptions.RequestException as e:
            logger.warning("Alpha Vantage 요청 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return {}
        except (ValueError, KeyError) as e:
            logger.warning("Alpha Vantage 데이터 파싱 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return {}
        except Exception as e:
            logger.warning("Alpha Vantage 예상치 못한 오류", symbol=symbol, exception=e, component="StockDataCollector")
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
                
        except requests.exceptions.Timeout as e:
            logger.warning("Alpha Vantage 일별 데이터 타임아웃", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            logger.warning("Alpha Vantage 일별 데이터 요청 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except (ValueError, KeyError) as e:
            logger.warning("Alpha Vantage 일별 데이터 파싱 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except Exception as e:
            logger.warning("Alpha Vantage 일별 데이터 예상치 못한 오류", symbol=symbol, exception=e, component="StockDataCollector")
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
                
        except requests.exceptions.Timeout as e:
            logger.warning("Alpha Vantage 일별 데이터 타임아웃", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            logger.warning("Alpha Vantage 일별 데이터 요청 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except (ValueError, KeyError) as e:
            logger.warning("Alpha Vantage 일별 데이터 파싱 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except Exception as e:
            logger.warning("Alpha Vantage 일별 데이터 예상치 못한 오류", symbol=symbol, exception=e, component="StockDataCollector")
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
                
        except requests.exceptions.Timeout as e:
            logger.warning("Alpha Vantage 일별 데이터 타임아웃", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            logger.warning("Alpha Vantage 일별 데이터 요청 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except (ValueError, KeyError) as e:
            logger.warning("Alpha Vantage 일별 데이터 파싱 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except Exception as e:
            logger.warning("Alpha Vantage 일별 데이터 예상치 못한 오류", symbol=symbol, exception=e, component="StockDataCollector")
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
                
        except requests.exceptions.Timeout as e:
            logger.warning("Alpha Vantage 일별 데이터 타임아웃", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            logger.warning("Alpha Vantage 일별 데이터 요청 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except (ValueError, KeyError) as e:
            logger.warning("Alpha Vantage 일별 데이터 파싱 오류", symbol=symbol, exception=e, component="StockDataCollector")
            return pd.DataFrame()
        except Exception as e:
            logger.warning("Alpha Vantage 일별 데이터 예상치 못한 오류", symbol=symbol, exception=e, component="StockDataCollector")
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
        np.random.seed(hash(symbol) % 2**32)
        
        symbol_hash = hash(symbol) % 1000
        base_price = 50 + (symbol_hash % 500)
        
        if symbol in self.mock_data_cache:
            base_data = self.mock_data_cache[symbol]
            previous_price = base_data['price']
            previous_change = base_data.get('change_percent', 0)
            
            market_trend = np.sin(time.time() / 86400) * 0.1
            volatility = 0.02 + (symbol_hash % 10) / 1000
            momentum = previous_change / 100 * 0.3
            
            price_change = np.random.normal(market_trend + momentum, volatility)
            new_price = previous_price * (1 + price_change)
            new_change_percent = previous_change * 0.7 + price_change * 100 * 0.3
        else:
            market_trend = np.sin(time.time() / 86400) * 0.1
            volatility = 0.02 + (symbol_hash % 10) / 1000
            
            price_change = np.random.normal(market_trend, volatility)
            new_price = base_price * (1 + price_change)
            new_change_percent = price_change * 100
        
        volume_base = 1000000 + (symbol_hash % 4000000)
        volume_multiplier = 1 + abs(new_change_percent / 100) * 5
        volume = int(volume_base * volume_multiplier)
        
        market_cap_base = 1000000000 + symbol_hash * 1000000
        market_cap = int(new_price * market_cap_base / base_price)
        
        pe_ratio = 15 + (symbol_hash % 20) + np.random.normal(0, 2)
        
        high_52w = new_price * (1.1 + (symbol_hash % 40) / 100)
        low_52w = new_price * (0.5 + (symbol_hash % 40) / 100)
        
        mock_data = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'price': float(max(0.01, new_price)),
            'volume': max(100000, volume),
            'change': float(new_price * new_change_percent / 100),
            'change_percent': float(new_change_percent),
            'market_cap': market_cap,
            'pe_ratio': float(max(5, min(50, pe_ratio))),
            'high_52w': float(high_52w),
            'low_52w': float(low_52w),
            'confidence_score': 0.3
        }
        
        self.mock_data_cache[symbol] = mock_data
        return mock_data
    
    def _generate_mock_historical_data(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        days = 30 if period == "1mo" else 90 if period == "3mo" else 7
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        np.random.seed(hash(symbol) % 2**32)
        
        symbol_hash = hash(symbol) % 1000
        base_price = 50 + (symbol_hash % 500)
        
        trend = np.sin(np.linspace(0, 2 * np.pi, len(dates))) * 0.05
        volatility = 0.02 + (symbol_hash % 10) / 1000
        
        price_changes = np.random.normal(trend, volatility, len(dates))
        prices = base_price * np.exp(np.cumsum(price_changes))
        
        opens = prices * (1 + np.random.normal(0, 0.01, len(dates)))
        highs = np.maximum(opens, prices) * (1 + np.random.uniform(0, 0.02, len(dates)))
        lows = np.minimum(opens, prices) * (1 - np.random.uniform(0, 0.02, len(dates)))
        closes = prices
        
        volume_base = 1000000 + (symbol_hash % 4000000)
        daily_volatility = np.abs(np.diff(prices, prepend=prices[0])) / prices
        volumes = (volume_base * (1 + daily_volatility * 10 + np.random.normal(0, 0.2, len(dates)))).astype(int)
        volumes = np.maximum(100000, volumes)
        
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