import requests
import logging
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import re
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
from config.settings import settings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logging.debug("googletrans 모듈이 설치되지 않았습니다. 번역 기능이 비활성화됩니다.")

try:
    from transformers import pipeline
    import torch
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    logging.debug("transformers 모듈이 설치되지 않았습니다. Hugging Face 번역 기능이 비활성화됩니다.")

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
        
        if GOOGLETRANS_AVAILABLE:
            try:
                self.translator = Translator()
            except Exception as e:
                logging.warning(f"번역기 초기화 실패: {str(e)}")
                self.translator = None
        else:
            self.translator = None
        
        self.hf_translator = None
        if HUGGINGFACE_AVAILABLE:
            try:
                self.hf_translator = pipeline(
                    "translation",
                    model="Helsinki-NLP/opus-mt-en-ko",
                    device=0 if torch.cuda.is_available() else -1
                )
                logging.info("Hugging Face 번역 모델 로드 완료")
            except Exception as e:
                logging.warning(f"Hugging Face 번역 모델 초기화 실패: {str(e)}")
                self.hf_translator = None
        else:
            logging.debug("Hugging Face 번역 모델을 사용할 수 없습니다. googletrans를 사용합니다.")
        
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
            
            if response.status_code == 404:
                logging.debug(f"Yahoo Finance News not found for {symbol}: 404")
                return []
            
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
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 404:
                logging.debug(f"Yahoo Finance News not found for {symbol}")
            else:
                logging.warning(f"Yahoo Finance News HTTP error for {symbol}: {e.response.status_code if e.response else 'Unknown'}")
            return []
        except Exception as e:
            logging.warning(f"Yahoo Finance News error for {symbol}: {str(e)}")
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
            
            try:
                soup = BeautifulSoup(response.text, 'xml')
            except Exception as parser_error:
                try:
                    soup = BeautifulSoup(response.text, 'lxml-xml')
                except Exception:
                    try:
                        soup = BeautifulSoup(response.text, 'html.parser')
                    except Exception as e:
                        logging.error(f"XML 파서 초기화 실패: {str(e)}")
                        return []
            
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
    
    def get_stock_news(self, symbol: str, include_korean: bool = False, auto_translate: bool = True) -> List[Dict]:
        cache_key = f"{symbol}_{include_korean}_{auto_translate}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                return cached_data
        
        all_news = []
        
        if include_korean:
            try:
                korean_query = self._get_korean_symbol_name(symbol)
                if korean_query:
                    naver_news = self.get_naver_news(korean_query)
                    all_news.extend(naver_news)
            except:
                pass
        
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
        
        if auto_translate:
            translated_news = []
            for news in all_news:
                provider = news.get('provider', '')
                if provider in ['newsapi', 'alphavantage', 'yahoo', 'google']:
                    translated = self.translate_news(news, translate_to_korean=True)
                    translated_news.append(translated)
                else:
                    translated_news.append(news)
            all_news = translated_news
        
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
    
    def _is_korean_text(self, text: str) -> bool:
        if not text:
            return False
        korean_char_count = sum(1 for char in text if '\uAC00' <= char <= '\uD7A3')
        total_char_count = len([c for c in text if c.isalnum() or c.isspace()])
        if total_char_count == 0:
            return False
        korean_ratio = korean_char_count / total_char_count if total_char_count > 0 else 0
        return korean_ratio > 0.3
    
    def translate_text(self, text: str, target_lang: str = 'ko') -> str:
        if not text:
            return text
        
        if target_lang == 'ko':
            if self._is_korean_text(text):
                logging.debug(f"이미 한글 텍스트입니다. 번역을 건너뜁니다.")
                return text
        
        if target_lang == 'ko' and self.hf_translator:
            try:
                if len(text) > 500:
                    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
                    translated_chunks = []
                    for chunk in chunks:
                        if self._is_korean_text(chunk):
                            translated_chunks.append(chunk)
                        else:
                            result = self.hf_translator(chunk)
                            translated_chunks.append(result[0]['translation_text'])
                    return ' '.join(translated_chunks)
                else:
                    if self._is_korean_text(text):
                        return text
                    result = self.hf_translator(text)
                    return result[0]['translation_text']
            except Exception as e:
                logging.warning(f"Hugging Face 번역 실패: {str(e)}")
                if self.translator:
                    pass
                else:
                    return text
        
        if self.translator:
            try:
                if self._is_korean_text(text) and target_lang == 'ko':
                    return text
                
                if len(text) > 5000:
                    text = text[:5000]
                
                result = self.translator.translate(text, dest=target_lang)
                if result and hasattr(result, 'text'):
                    translated = result.text
                    if translated and translated != text:
                        return translated
                return text
            except Exception as e:
                logging.warning(f"googletrans 번역 실패: {str(e)}")
                return text
        
        if not self.hf_translator and not self.translator:
            logging.debug("번역 모듈이 설치되지 않았습니다. 원문을 반환합니다.")
        
        return text
    
    def translate_news(self, news: Dict, translate_to_korean: bool = True) -> Dict:
        if not translate_to_korean:
            return news
        
        translated_news = news.copy()
        
        title = news.get('title', '')
        description = news.get('description', '')
        
        if title:
            try:
                if self._is_korean_text(title):
                    translated_news['title_ko'] = title
                    translated_news['title_original'] = title
                else:
                    if self.hf_translator or self.translator:
                        translated_title = self.translate_text(title, 'ko')
                        translated_news['title_ko'] = translated_title if translated_title else title
                        translated_news['title_original'] = title
                    else:
                        translated_news['title_ko'] = title
                        translated_news['title_original'] = title
            except Exception as e:
                logging.warning(f"제목 번역 실패: {str(e)}")
                translated_news['title_ko'] = title
                translated_news['title_original'] = title
        
        if description:
            try:
                if self._is_korean_text(description):
                    translated_news['description_ko'] = description
                    translated_news['description_original'] = description
                else:
                    if self.hf_translator or self.translator:
                        translated_desc = self.translate_text(description, 'ko')
                        translated_news['description_ko'] = translated_desc if translated_desc else description
                        translated_news['description_original'] = description
                    else:
                        translated_news['description_ko'] = description
                        translated_news['description_original'] = description
            except Exception as e:
                logging.warning(f"설명 번역 실패: {str(e)}")
                translated_news['description_ko'] = description
                translated_news['description_original'] = description
        
        return translated_news
    
    def get_stock_news_with_translation(self, symbol: str, include_korean: bool = False, translate_to_korean: bool = True) -> List[Dict]:
        news_list = self.get_stock_news(symbol, include_korean)
        
        if translate_to_korean and (self.hf_translator or self.translator):
            translated_news = []
            for news in news_list:
                if news.get('provider') in ['newsapi', 'alphavantage', 'yahoo', 'google']:
                    translated = self.translate_news(news, translate_to_korean=True)
                    translated_news.append(translated)
                else:
                    translated_news.append(news)
            return translated_news
        
        return news_list
    
    def get_news_by_url(self, url: str) -> Optional[Dict]:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = None
            title_selectors = [
                'meta[property="og:title"]',
                'meta[name="twitter:title"]',
                'h1.article-title',
                'h1.headline',
                'h1.post-title',
                'h1.entry-title',
                'h1',
                '.article-title',
                '.headline',
                '.post-title',
                '.entry-title'
            ]
            for selector in title_selectors:
                if selector.startswith('meta'):
                    meta = soup.select_one(selector)
                    if meta:
                        title = meta.get('content', '')
                        break
                else:
                    elem = soup.select_one(selector)
                    if elem:
                        title = elem.get_text(strip=True)
                        break
            
            if not title:
                title = soup.find('title')
                title = title.get_text(strip=True) if title else '제목 없음'
            
            description = None
            desc_selectors = [
                'meta[property="og:description"]',
                'meta[name="description"]',
                'meta[name="twitter:description"]',
                '.article-summary',
                '.article-description',
                '.summary',
                '.excerpt',
                '.post-excerpt',
                '.entry-summary'
            ]
            for selector in desc_selectors:
                if selector.startswith('meta'):
                    meta = soup.select_one(selector)
                    if meta:
                        description = meta.get('content', '')
                        break
                else:
                    elem = soup.select_one(selector)
                    if elem:
                        description = elem.get_text(strip=True)
                        break
            
            content = None
            content_selectors = [
                'article .article-content',
                'article .article-body',
                'article .post-content',
                'article .entry-content',
                '.article-content',
                '.article-body',
                '.post-content',
                '.entry-content',
                '.content-body',
                '.story-body',
                '.article-text',
                '[data-module="ArticleBody"]',
                '.article-body-content',
                '.post-body',
                '.entry-body',
                'article',
                '.content',
                'main article',
                'main .content',
                '#article-body',
                '.article-main-content'
            ]
            for selector in content_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        for script in elem(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                            script.decompose()
                        for ad in elem.find_all(['div'], class_=lambda x: x and ('ad' in x.lower() or 'advertisement' in x.lower() or 'sponsor' in x.lower())):
                            ad.decompose()
                        content = elem.get_text(separator='\n', strip=True)
                        if len(content) > 100:
                            break
                except Exception as e:
                    logging.debug(f"셀렉터 {selector} 실패: {str(e)}")
                    continue
            
            source = None
            source_selectors = [
                'meta[property="og:site_name"]',
                'meta[name="author"]',
                '.article-source',
                '.source',
                '.author',
                '.byline',
                '.article-author',
                '.post-author'
            ]
            for selector in source_selectors:
                if selector.startswith('meta'):
                    meta = soup.select_one(selector)
                    if meta:
                        source = meta.get('content', '')
                        break
                else:
                    elem = soup.select_one(selector)
                    if elem:
                        source = elem.get_text(strip=True)
                        break
            
            published_at = None
            time_selectors = [
                'meta[property="article:published_time"]',
                'time[datetime]', '.published-date', '.date'
            ]
            for selector in time_selectors:
                if selector.startswith('meta'):
                    meta = soup.select_one(selector)
                    if meta:
                        published_at = meta.get('content', '')
                        break
                else:
                    elem = soup.select_one(selector)
                    if elem:
                        if elem.get('datetime'):
                            published_at = elem.get('datetime')
                        else:
                            published_at = elem.get_text(strip=True)
                        break
            
            title_ko = None
            description_ko = None
            content_ko = None
            try:
                if self._is_korean_text(title):
                    title_ko = title
                else:
                    title_ko = self.translate_text(title, 'ko') if (self.hf_translator or self.translator) else title
                
                if description:
                    if self._is_korean_text(description):
                        description_ko = description
                    else:
                        description_ko = self.translate_text(description, 'ko') if (self.hf_translator or self.translator) else description
                
                if content:
                    content_preview = content[:500] if len(content) > 500 else content
                    if self._is_korean_text(content_preview):
                        content_ko = content_preview
                    else:
                        content_ko = self.translate_text(content_preview, 'ko') if (self.hf_translator or self.translator) else content_preview
            except Exception as e:
                logging.warning(f"뉴스 번역 실패: {str(e)}")
                title_ko = title
                description_ko = description
                content_ko = None
            
            news_data = {
                'title': title or '제목 없음',
                'title_ko': title_ko or title or '제목 없음',
                'title_original': title or '제목 없음',
                'description': description or '',
                'description_ko': description_ko or description or '',
                'description_original': description or '',
                'content': content or '',
                'content_ko': content_ko or '',
                'url': url,
                'source': source or '알 수 없음',
                'published_at': published_at or '',
                'provider': 'web_scraping',
                'symbol': ''
            }
            
            return news_data
            
        except Exception as e:
            logging.error(f"뉴스 URL 조회 실패 ({url}): {str(e)}")
            return None

