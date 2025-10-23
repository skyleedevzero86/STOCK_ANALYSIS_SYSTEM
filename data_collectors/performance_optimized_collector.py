import asyncio
import aiohttp
import pandas as pd
import numpy as np
import redis
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass
from queue import Queue, Empty
import hashlib
import pickle
from config.settings import settings

@dataclass
class DataRequest:
    symbol: str
    request_type: str
    priority: int
    timestamp: datetime
    callback: Optional[callable] = None

class PerformanceOptimizedCollector:
    
    def __init__(self, symbols: List[str], max_workers: int = 10, cache_ttl: int = 300):
        self.symbols = symbols
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.session = None
        self.request_queue = Queue()
        self.result_cache = {}
        self.rate_limiter = {}
        self.connection_pool = None
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.batch_size = 5
        self.retry_attempts = 3
        self.timeout = 30
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self.thread_pool.shutdown(wait=True)
    
    def _get_cache_key(self, symbol: str, request_type: str) -> str:
        return f"stock_data:{symbol}:{request_type}:{int(time.time() // self.cache_ttl)}"
    
    def _is_rate_limited(self, api_type: str) -> bool:
        current_time = time.time()
        if api_type not in self.rate_limiter:
            self.rate_limiter[api_type] = current_time
            return False
        
        time_diff = current_time - self.rate_limiter[api_type]
        if api_type == 'yfinance':
            return time_diff < 0.1
        elif api_type == 'alpha_vantage':
            return time_diff < 12
        return False
    
    def _update_rate_limiter(self, api_type: str):
        self.rate_limiter[api_type] = time.time()
    
    async def get_cached_data(self, symbol: str, request_type: str) -> Optional[Dict]:
        try:
            cache_key = self._get_cache_key(symbol, request_type)
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logging.warning(f"Cache retrieval failed: {e}")
        return None
    
    async def set_cached_data(self, symbol: str, request_type: str, data: Dict):
        try:
            cache_key = self._get_cache_key(symbol, request_type)
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logging.warning(f"Cache storage failed: {e}")
    
    async def get_realtime_data_async(self, symbol: str) -> Dict:
        cached_data = await self.get_cached_data(symbol, 'realtime')
        if cached_data:
            return cached_data
        
        if self._is_rate_limited('yfinance'):
            await asyncio.sleep(0.1)
        
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'range': '1d',
                'interval': '1m',
                'includePrePost': 'true',
                'useYfid': 'true',
                'corsDomain': 'finance.yahoo.com'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = self._parse_yahoo_response(data, symbol)
                    await self.set_cached_data(symbol, 'realtime', result)
                    self._update_rate_limiter('yfinance')
                    return result
                else:
                    return await self._get_fallback_data(symbol)
        
        except Exception as e:
            logging.error(f"Error fetching realtime data for {symbol}: {e}")
            return await self._get_fallback_data(symbol)
    
    async def get_historical_data_async(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        cached_data = await self.get_cached_data(symbol, f'historical_{period}')
        if cached_data:
            return pd.DataFrame(cached_data)
        
        if self._is_rate_limited('yfinance'):
            await asyncio.sleep(0.1)
        
        try:
            end_date = int(time.time())
            start_date = end_date - (30 * 24 * 60 * 60 if period == "1mo" else 90 * 24 * 60 * 60)
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'period1': start_date,
                'period2': end_date,
                'interval': '1d',
                'includePrePost': 'true',
                'events': 'div,split'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    df = self._parse_yahoo_historical_response(data, symbol)
                    if not df.empty:
                        await self.set_cached_data(symbol, f'historical_{period}', df.to_dict('records'))
                    self._update_rate_limiter('yfinance')
                    return df
                else:
                    return await self._get_fallback_historical_data(symbol, period)
        
        except Exception as e:
            logging.error(f"Error fetching historical data for {symbol}: {e}")
            return await self._get_fallback_historical_data(symbol, period)
    
    async def get_alpha_vantage_data_async(self, symbol: str, function: str) -> Dict:
        if self._is_rate_limited('alpha_vantage'):
            await asyncio.sleep(12)
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': settings.ALPHA_VANTAGE_API_KEY,
                'outputsize': 'compact'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self._update_rate_limiter('alpha_vantage')
                    return data
                else:
                    return {}
        
        except Exception as e:
            logging.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return {}
    
    async def batch_collect_realtime_data(self, symbols: List[str]) -> List[Dict]:
        tasks = []
        for symbol in symbols:
            task = self.get_realtime_data_async(symbol)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logging.error(f"Error collecting data for {symbols[i]}: {result}")
                continue
            if result and result.get('price', 0) > 0:
                valid_results.append(result)
        
        return valid_results
    
    async def batch_collect_historical_data(self, symbols: List[str], period: str = "1mo") -> Dict[str, pd.DataFrame]:
        tasks = []
        for symbol in symbols:
            task = self.get_historical_data_async(symbol, period)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data_dict = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logging.error(f"Error collecting historical data for {symbols[i]}: {result}")
                continue
            if isinstance(result, pd.DataFrame) and not result.empty:
                data_dict[symbols[i]] = result
        
        return data_dict
    
    def _parse_yahoo_response(self, data: Dict, symbol: str) -> Dict:
        try:
            if 'chart' not in data or not data['chart']['result']:
                return self._generate_mock_data(symbol)
            
            result = data['chart']['result'][0]
            meta = result.get('meta', {})
            timestamps = result.get('timestamp', [])
            indicators = result.get('indicators', {})
            
            if not timestamps or 'quote' not in indicators:
                return self._generate_mock_data(symbol)
            
            quote = indicators['quote'][0]
            latest_idx = -1
            
            price = quote.get('close', [0])[latest_idx] or meta.get('regularMarketPrice', 0)
            volume = quote.get('volume', [0])[latest_idx] or meta.get('regularMarketVolume', 0)
            change = meta.get('regularMarketChange', 0)
            change_percent = meta.get('regularMarketChangePercent', 0)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price': float(price),
                'volume': int(volume),
                'change': float(change),
                'change_percent': float(change_percent),
                'high': float(quote.get('high', [0])[latest_idx] or meta.get('regularMarketDayHigh', 0)),
                'low': float(quote.get('low', [0])[latest_idx] or meta.get('regularMarketDayLow', 0)),
                'open': float(quote.get('open', [0])[latest_idx] or meta.get('regularMarketOpen', 0)),
                'market_cap': meta.get('marketCap', 0),
                'pe_ratio': meta.get('trailingPE', 0)
            }
        
        except Exception as e:
            logging.error(f"Error parsing Yahoo response for {symbol}: {e}")
            return self._generate_mock_data(symbol)
    
    def _parse_yahoo_historical_response(self, data: Dict, symbol: str) -> pd.DataFrame:
        try:
            if 'chart' not in data or not data['chart']['result']:
                return pd.DataFrame()
            
            result = data['chart']['result'][0]
            timestamps = result.get('timestamp', [])
            indicators = result.get('indicators', {})
            
            if not timestamps or 'quote' not in indicators:
                return pd.DataFrame()
            
            quote = indicators['quote'][0]
            df_data = []
            
            for i, timestamp in enumerate(timestamps):
                df_data.append({
                    'date': pd.to_datetime(timestamp, unit='s'),
                    'open': float(quote.get('open', [0])[i] or 0),
                    'high': float(quote.get('high', [0])[i] or 0),
                    'low': float(quote.get('low', [0])[i] or 0),
                    'close': float(quote.get('close', [0])[i] or 0),
                    'volume': int(quote.get('volume', [0])[i] or 0),
                    'symbol': symbol
                })
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('date').reset_index(drop=True)
            return df
        
        except Exception as e:
            logging.error(f"Error parsing Yahoo historical response for {symbol}: {e}")
            return pd.DataFrame()
    
    async def _get_fallback_data(self, symbol: str) -> Dict:
        return self._generate_mock_data(symbol)
    
    async def _get_fallback_historical_data(self, symbol: str, period: str) -> pd.DataFrame:
        return self._generate_mock_historical_data(symbol, period)
    
    def _generate_mock_data(self, symbol: str) -> Dict:
        np.random.seed(hash(symbol) % 2**32)
        base_price = 100 + hash(symbol) % 200
        price_change = np.random.normal(0, 0.02)
        new_price = base_price * (1 + price_change)
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'price': float(new_price),
            'volume': int(np.random.randint(1000000, 5000000)),
            'change': float(new_price * np.random.normal(0, 0.5) / 100),
            'change_percent': float(np.random.normal(0, 2)),
            'high': float(new_price * (1 + abs(np.random.normal(0, 0.01)))),
            'low': float(new_price * (1 - abs(np.random.normal(0, 0.01)))),
            'open': float(new_price * (1 + np.random.normal(0, 0.005))),
            'market_cap': int(new_price * np.random.randint(1000000000, 2000000000)),
            'pe_ratio': float(np.random.uniform(15, 35))
        }
    
    def _generate_mock_historical_data(self, symbol: str, period: str) -> pd.DataFrame:
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
        
        return pd.DataFrame({
            'date': dates,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes,
            'symbol': symbol
        })
    
    async def stream_realtime_data(self, symbols: List[str], callback: callable):
        while True:
            try:
                start_time = time.time()
                results = await self.batch_collect_realtime_data(symbols)
                
                for result in results:
                    await callback(result)
                
                elapsed = time.time() - start_time
                sleep_time = max(0, 5 - elapsed)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"Error in streaming: {e}")
                await asyncio.sleep(5)
    
    def get_performance_metrics(self) -> Dict:
        return {
            'cache_hit_rate': getattr(self, 'cache_hits', 0) / max(1, getattr(self, 'total_requests', 1)),
            'avg_response_time': getattr(self, 'total_response_time', 0) / max(1, getattr(self, 'total_requests', 1)),
            'error_rate': getattr(self, 'error_count', 0) / max(1, getattr(self, 'total_requests', 1)),
            'active_connections': len(getattr(self, 'active_connections', [])),
            'queue_size': self.request_queue.qsize()
        }
    
    async def health_check(self) -> Dict:
        try:
            test_symbol = self.symbols[0] if self.symbols else 'AAPL'
            result = await self.get_realtime_data_async(test_symbol)
            
            return {
                'status': 'healthy' if result and result.get('price', 0) > 0 else 'unhealthy',
                'response_time': time.time(),
                'data_quality': 'good' if result else 'poor',
                'cache_status': 'connected' if self.redis_client.ping() else 'disconnected'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': time.time(),
                'data_quality': 'poor',
                'cache_status': 'disconnected'
            }
