import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import re
from bs4 import BeautifulSoup
from config.settings import settings

class NewsCollector:
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.newsapi_key = getattr(settings, 'NEWSAPI_KEY', None)
        self.alpha_vantage_api_key = settings.ALPHA_VANTAGE_API_KEY
        self.cache = {}
        self.cache_ttl = 300
        
    def get_newsapi_news(self, symbol: str, language: str = 'en', page_size: int = 10) -> List[Dict]:
        if not self.newsapi_key:
            return []
            
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': symbol,
                'language': language,
                'sortBy': 'publishedAt',
                'pageSize': page_size,
                'apiKey': self.newsapi_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok':
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'published_at': article.get('publishedAt', ''),
                        'symbol': symbol,
                        'provider': 'newsapi'
                    })
                return articles
            return []
            
        except Exception as e:
            logging.error(f"NewsAPI error for {symbol}: {str(e)}")
            return []
    
    def get_alpha_vantage_news(self, symbol: str) -> List[Dict]:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': symbol,
                'apikey': self.alpha_vantage_api_key,
                'limit': 10
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'feed' in data:
                articles = []
                for item in data['feed']:
                    articles.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'source': item.get('source', ''),
                        'published_at': item.get('time_published', ''),
                        'summary': item.get('summary', ''),
                        'sentiment': item.get('overall_sentiment_score', 0),
                        'symbol': symbol,
                        'provider': 'alphavantage'
                    })
                return articles
            return []
            
        except Exception as e:
            logging.error(f"Alpha Vantage News error for {symbol}: {str(e)}")
            return []
    
    def get_yahoo_finance_news(self, symbol: str) -> List[Dict]:
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            news_items = soup.find_all('div', class_='js-stream-content')
            for item in news_items[:10]:
                title_elem = item.find('h3')
                link_elem = item.find('a')
                time_elem = item.find('time')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get('href', '')
                    if url and not url.startswith('http'):
                        url = f"https://finance.yahoo.com{url}"
                    
                    published_at = ''
                    if time_elem:
                        published_at = time_elem.get('datetime', '')
                    
                    articles.append({
                        'title': title,
                        'url': url,
                        'published_at': published_at,
                        'symbol': symbol,
                        'provider': 'yahoo'
                    })
            
            return articles
            
        except Exception as e:
            logging.error(f"Yahoo Finance News error for {symbol}: {str(e)}")
            return []
    
    def get_naver_news(self, query: str, max_results: int = 10) -> List[Dict]:
        try:
            url = "https://search.naver.com/search.naver"
            params = {
                'where': 'news',
                'query': query,
                'sm': 'tab_jum',
                'sort': 1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            news_items = soup.find_all('div', class_='news_area')
            for item in news_items[:max_results]:
                title_elem = item.find('a', class_='news_tit')
                desc_elem = item.find('div', class_='news_dsc')
                info_elem = item.find('span', class_='info')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    description = ''
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                    
                    published_at = ''
                    if info_elem:
                        published_at = info_elem.get_text(strip=True)
                    
                    articles.append({
                        'title': title,
                        'description': description,
                        'url': url,
                        'published_at': published_at,
                        'symbol': query,
                        'provider': 'naver'
                    })
            
            return articles
            
        except Exception as e:
            logging.error(f"Naver News error for {query}: {str(e)}")
            return []
    
    def get_google_news_rss(self, symbol: str, language: str = 'en') -> List[Dict]:
        try:
            url = "https://news.google.com/rss"
            params = {
                'q': symbol,
                'hl': language,
                'gl': 'US' if language == 'en' else 'KR',
                'ceid': 'US:en' if language == 'en' else 'KR:ko'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'xml')
            articles = []
            
            items = soup.find_all('item')
            for item in items[:10]:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                description = item.find('description')
                
                if title and link:
                    articles.append({
                        'title': title.get_text(strip=True) if title else '',
                        'url': link.get_text(strip=True) if link else '',
                        'published_at': pub_date.get_text(strip=True) if pub_date else '',
                        'description': description.get_text(strip=True) if description else '',
                        'symbol': symbol,
                        'provider': 'google'
                    })
            
            return articles
            
        except Exception as e:
            logging.error(f"Google News RSS error for {symbol}: {str(e)}")
            return []
    
    def get_stock_news(self, symbol: str, include_korean: bool = False) -> List[Dict]:
        cache_key = f"{symbol}_{include_korean}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                return cached_data
        
        all_news = []
        
        try:
            newsapi_news = self.get_newsapi_news(symbol)
            all_news.extend(newsapi_news)
            time.sleep(0.5)
        except:
            pass
        
        try:
            alpha_news = self.get_alpha_vantage_news(symbol)
            all_news.extend(alpha_news)
            time.sleep(0.5)
        except:
            pass
        
        try:
            yahoo_news = self.get_yahoo_finance_news(symbol)
            all_news.extend(yahoo_news)
            time.sleep(0.5)
        except:
            pass
        
        try:
            google_news = self.get_google_news_rss(symbol)
            all_news.extend(google_news)
        except:
            pass
        
        if include_korean:
            try:
                korean_query = self._get_korean_symbol_name(symbol)
                if korean_query:
                    naver_news = self.get_naver_news(korean_query)
                    all_news.extend(naver_news)
            except:
                pass
        
        all_news = sorted(all_news, key=lambda x: x.get('published_at', ''), reverse=True)
        
        self.cache[cache_key] = (all_news, datetime.now())
        
        return all_news
    
    def get_multiple_stock_news(self, symbols: List[str], include_korean: bool = False) -> Dict[str, List[Dict]]:
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_news(symbol, include_korean)
            time.sleep(1)
        return results
    
    def _get_korean_symbol_name(self, symbol: str) -> Optional[str]:
        symbol_map = {
            'AAPL': '애플',
            'GOOGL': '구글',
            'MSFT': '마이크로소프트',
            'AMZN': '아마존',
            'TSLA': '테슬라',
            'NVDA': '엔비디아',
            'META': '메타',
            'NFLX': '넷플릭스'
        }
        return symbol_map.get(symbol, symbol)
    
    def search_news(self, query: str, language: str = 'en', max_results: int = 20) -> List[Dict]:
        all_news = []
        
        try:
            if self.newsapi_key:
                newsapi_news = self.get_newsapi_news(query, language=language, page_size=max_results)
                all_news.extend(newsapi_news)
        except:
            pass
        
        try:
            google_news = self.get_google_news_rss(query, language=language)
            all_news.extend(google_news[:max_results])
        except:
            pass
        
        if language == 'ko':
            try:
                naver_news = self.get_naver_news(query, max_results=max_results)
                all_news.extend(naver_news)
            except:
                pass
        
        all_news = sorted(all_news, key=lambda x: x.get('published_at', ''), reverse=True)
        return all_news[:max_results]

