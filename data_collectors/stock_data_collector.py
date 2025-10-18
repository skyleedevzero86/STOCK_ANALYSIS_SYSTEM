import yfinance as yf
import pandas as pd
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class StockDataCollector:
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.session = requests.Session()
        
    def get_historical_data(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                logging.warning(f"{symbol}: 데이터가 없습니다")
                return pd.DataFrame()
                
            data.reset_index(inplace=True)
            data.columns = [col.lower().replace(' ', '_') for col in data.columns]
            
            data['symbol'] = symbol
            
            logging.info(f"{symbol}: {len(data)}일 데이터 수집 완료")
            return data
            
        except Exception as e:
            logging.error(f"{symbol} 데이터 수집 실패: {str(e)}")
            return pd.DataFrame()
    
    def get_realtime_data(self, symbol: str) -> Dict:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                latest_price = hist['Close'].iloc[-1]
                volume = hist['Volume'].iloc[-1]
            else:
                latest_price = info.get('currentPrice', 0)
                volume = info.get('volume', 0)
            
            realtime_data = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price': float(latest_price),
                'volume': int(volume),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'high_52w': info.get('fiftyTwoWeekHigh', 0),
                'low_52w': info.get('fiftyTwoWeekLow', 0)
            }
            
            return realtime_data
            
        except Exception as e:
            logging.error(f"{symbol} 실시간 데이터 수집 실패: {str(e)}")
            return {}
    
    def get_multiple_realtime_data(self) -> List[Dict]:
        results = []
        
        for symbol in self.symbols:
            data = self.get_realtime_data(symbol)
            if data:
                results.append(data)
            time.sleep(0.1)
            
        return results
    
    def get_alpha_vantage_data(self, symbol: str, api_key: str) -> Dict:
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': api_key
            }
            
            response = self.session.get(url, params=params)
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                return {
                    'symbol': symbol,
                    'price': float(quote.get('05. price', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                    'volume': int(quote.get('06. volume', 0)),
                    'high': float(quote.get('03. high', 0)),
                    'low': float(quote.get('04. low', 0)),
                    'open': float(quote.get('02. open', 0))
                }
            
        except Exception as e:
            logging.error(f"Alpha Vantage API 오류 ({symbol}): {str(e)}")
            
        return {}
    
    def collect_batch_data(self) -> Dict[str, pd.DataFrame]:
        all_data = {}
        
        for symbol in self.symbols:
            logging.info(f"{symbol} 데이터 수집 시작...")
            data = self.get_historical_data(symbol, period="3mo")
            
            if not data.empty:
                all_data[symbol] = data
            else:
                logging.warning(f"{symbol} 데이터 수집 실패")
                
            time.sleep(1)
            
        return all_data

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
