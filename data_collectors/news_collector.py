import requests
import logging
import time
import warnings
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import re
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
from config.settings import settings
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from functools import wraps

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

warnings.filterwarnings("ignore", message=".*Xet Storage.*")
warnings.filterwarnings("ignore", message=".*sacremoses.*")
warnings.filterwarnings("ignore", message=".*symlinks.*")

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logging.debug("googletrans 모듈이 설치되지 않았습니다. 번역 기능이 비활성화됩니다.")

try:
    from transformers import pipeline, T5TokenizerFast
    import torch
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    logging.debug("transformers 모듈이 설치되지 않았습니다. Hugging Face 번역 기능이 비활성화됩니다.")

def retry_with_backoff(max_retries=3, initial_delay=1, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logging.warning(f"{func.__name__} 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}. {delay}초 후 재시도...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logging.error(f"{func.__name__} 최종 실패: {str(e)}")
            raise last_exception
        return wrapper
    return decorator

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
        self.max_workers = 5
        
        self.hf_translator = None
        self.translator = None
        
        if HUGGINGFACE_AVAILABLE:
            try:
                tokenizer_name = "paust/pko-t5-base"
                model_path = "Darong/BlueT"
                tokenizer = T5TokenizerFast.from_pretrained(tokenizer_name)
                self.hf_translator = pipeline(
                    "translation",
                    model=model_path,
                    tokenizer=tokenizer,
                    max_length=255,
                    device=0 if torch.cuda.is_available() else -1
                )
                logging.info("Hugging Face BlueT 번역 모델 로드 완료")
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    logging.warning("Hugging Face Hub 접근 실패. 인터넷 연결 또는 인증 문제일 수 있습니다.")
                elif "Repository Not Found" in error_msg:
                    logging.warning("Hugging Face 모델을 찾을 수 없습니다. 모델 이름을 확인하세요.")
                else:
                    logging.warning(f"Hugging Face 번역 모델 초기화 실패: {error_msg}")
                self.hf_translator = None
        
        if not self.hf_translator and GOOGLETRANS_AVAILABLE:
            try:
                self.translator = Translator()
                logging.info("googletrans 번역기 초기화 완료")
            except Exception as e:
                logging.warning(f"googletrans 번역기 초기화 실패: {str(e)}")
                self.translator = None
        
        if not self.hf_translator and not self.translator:
            logging.warning("번역 모델이 로드되지 않았습니다. 번역 기능이 비활성화됩니다.")
        
    @retry_with_backoff(max_retries=2, initial_delay=0.5)
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
            
            response = self.session.get(url, params=params, timeout=8)
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
            
        except requests.exceptions.Timeout:
            logging.warning(f"NewsAPI 타임아웃: {symbol}")
            return []
        except Exception as e:
            logging.error(f"{symbol}에 대한 NewsAPI 오류: {str(e)}")
            return []
    
    @retry_with_backoff(max_retries=2, initial_delay=0.5)
    def get_alpha_vantage_news(self, symbol: str) -> List[Dict]:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': symbol,
                'apikey': self.alpha_vantage_api_key,
                'limit': 10
            }
            
            response = self.session.get(url, params=params, timeout=8)
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
            
        except requests.exceptions.Timeout:
            logging.warning(f"Alpha Vantage 타임아웃: {symbol}")
            return []
        except Exception as e:
            logging.error(f"{symbol}에 대한 Alpha Vantage News 오류: {str(e)}")
            return []
    
    @retry_with_backoff(max_retries=2, initial_delay=0.5)
    def get_yahoo_finance_news(self, symbol: str) -> List[Dict]:
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            response = self.session.get(url, timeout=8)
            
            if response.status_code == 404:
                logging.debug(f"{symbol}에 대한 Yahoo Finance News를 찾을 수 없음: 404")
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
            
        except requests.exceptions.Timeout:
            logging.warning(f"Yahoo Finance 타임아웃: {symbol}")
            return []
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 404:
                logging.debug(f"{symbol}에 대한 Yahoo Finance News를 찾을 수 없음")
            else:
                logging.warning(f"{symbol}에 대한 Yahoo Finance News HTTP 오류: {e.response.status_code if e.response else '알 수 없음'}")
            return []
        except Exception as e:
            logging.warning(f"{symbol}에 대한 Yahoo Finance News 오류: {str(e)}")
            return []
    
    @retry_with_backoff(max_retries=2, initial_delay=0.5)
    def get_naver_news(self, query: str, max_results: int = 10) -> List[Dict]:
        try:
            url = "https://search.naver.com/search.naver"
            params = {
                'where': 'news',
                'query': query,
                'sm': 'tab_jum',
                'sort': 1
            }
            
            response = self.session.get(url, params=params, timeout=8)
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
            
        except requests.exceptions.Timeout:
            logging.warning(f"Naver News 타임아웃: {query}")
            return []
        except Exception as e:
            logging.error(f"{query}에 대한 Naver News 오류: {str(e)}")
            return []
    
    @retry_with_backoff(max_retries=2, initial_delay=0.5)
    def get_google_news_rss(self, symbol: str, language: str = 'en') -> List[Dict]:
        try:
            url = "https://news.google.com/rss"
            params = {
                'q': symbol,
                'hl': language,
                'gl': 'US' if language == 'en' else 'KR',
                'ceid': 'US:en' if language == 'en' else 'KR:ko'
            }
            
            response = self.session.get(url, params=params, timeout=8)
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
            
        except requests.exceptions.Timeout:
            logging.warning(f"Google News RSS 타임아웃: {symbol}")
            return []
        except Exception as e:
            logging.error(f"{symbol}에 대한 Google News RSS 오류: {str(e)}")
            return []
    
    def get_stock_news(self, symbol: str, include_korean: bool = False, auto_translate: bool = True) -> List[Dict]:
        start_time = time.time()
        logging.info(f"뉴스 수집 시작: {symbol} (include_korean={include_korean}, auto_translate={auto_translate})")
        
        cache_key = f"{symbol}_{include_korean}_{auto_translate}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                logging.info(f"캐시에서 뉴스 반환: {symbol} ({len(cached_data)}개)")
                return cached_data
        
        all_news = []
        
        tasks = []
        
        if include_korean:
            korean_query = self._get_korean_symbol_name(symbol)
            if korean_query:
                tasks.append(('naver', lambda: self.get_naver_news(korean_query)))
        
        tasks.append(('newsapi', lambda: self.get_newsapi_news(symbol)))
        tasks.append(('alphavantage', lambda: self.get_alpha_vantage_news(symbol)))
        tasks.append(('yahoo', lambda: self.get_yahoo_finance_news(symbol)))
        tasks.append(('google', lambda: self.get_google_news_rss(symbol)))
        
        logging.info(f"뉴스 소스 {len(tasks)}개 시작: {symbol}")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_source = {}
            for source_name, task_func in tasks:
                future = executor.submit(task_func)
                future_to_source[future] = source_name
            
            completed_count = 0
            try:
                for future in as_completed(future_to_source, timeout=15):
                    source_name = future_to_source[future]
                    try:
                        news_list = future.result(timeout=3)
                        if news_list:
                            all_news.extend(news_list)
                            logging.info(f"{source_name}에서 {len(news_list)}개 뉴스 수집 완료: {symbol}")
                        completed_count += 1
                    except FutureTimeoutError:
                        logging.warning(f"{source_name} 뉴스 수집 타임아웃")
                        completed_count += 1
                    except Exception as e:
                        logging.warning(f"{source_name} 뉴스 수집 실패: {str(e)}")
                        completed_count += 1
            except FutureTimeoutError:
                logging.warning(f"뉴스 수집 전체 타임아웃 발생. 완료된 작업만 사용합니다.")
                for future, source_name in future_to_source.items():
                    if future.done():
                        try:
                            news_list = future.result()
                            if news_list:
                                all_news.extend(news_list)
                                logging.info(f"{source_name}에서 {len(news_list)}개 뉴스 수집 완료 (타임아웃 후): {symbol}")
                        except Exception:
                            pass
            finally:
                for future in future_to_source.keys():
                    if not future.done():
                        future.cancel()
        
        collection_time = time.time() - start_time
        logging.info(f"뉴스 수집 완료: {symbol} - {len(all_news)}개 수집 (소요 시간: {collection_time:.2f}초)")
        
        if not all_news:
            logging.info(f"뉴스가 없습니다: {symbol}")
            return []
        
        if auto_translate and all_news:
            translate_start = time.time()
            if not self.hf_translator and not self.translator:
                logging.warning(f"번역 모델이 로드되지 않았습니다. 번역을 건너뜁니다: {symbol}")
                for news in all_news:
                    news['title_ko'] = news.get('title', '')
                    news['title_original'] = news.get('title', '')
                    news['description_ko'] = news.get('description', '')
                    news['description_original'] = news.get('description', '')
            else:
                for news in all_news:
                    news['title_ko'] = news.get('title', '')
                    news['title_original'] = news.get('title', '')
                    news['description_ko'] = news.get('description', '')
                    news['description_original'] = news.get('description', '')
                
                max_translate = min(3, len(all_news))
                timeout_seconds = 3 if len(all_news) <= 3 else 5
                logging.info(f"번역 시작: {symbol} - {max_translate}개 번역 시도 (전체 {len(all_news)}개 중, 타임아웃: {timeout_seconds}초)")
                translated_count = 0
                failed_count = 0
                
                def translate_news_item(news_item, index):
                    provider = news_item.get('provider', '')
                    if provider in ['newsapi', 'alphavantage', 'yahoo', 'google']:
                        title = news_item.get('title', '')
                        
                        if title and not self._is_korean_text(title):
                            try:
                                if self.hf_translator:
                                    prefix = "E2K: "
                                    result = self.hf_translator(prefix + title[:80], max_length=120)
                                    translated_title = result[0]['translation_text'] if isinstance(result, list) and len(result) > 0 else result.get('translation_text', title)
                                    all_news[index]['title_ko'] = translated_title
                                    all_news[index]['title_original'] = title
                                    return True
                                elif self.translator:
                                    result = self.translator.translate(title[:150], dest='ko')
                                    translated_title = result.text if hasattr(result, 'text') else str(result)
                                    all_news[index]['title_ko'] = translated_title
                                    all_news[index]['title_original'] = title
                                    return True
                            except Exception:
                                pass
                    return False
                
                if max_translate > 0:
                    with ThreadPoolExecutor(max_workers=min(2, max_translate)) as executor:
                        future_to_index = {}
                        for i in range(max_translate):
                            future = executor.submit(translate_news_item, all_news[i], i)
                            future_to_index[future] = i
                        
                        completed_futures = set()
                        try:
                            for future in as_completed(future_to_index, timeout=timeout_seconds):
                                completed_futures.add(future)
                                try:
                                    success = future.result(timeout=0.3)
                                    if success:
                                        translated_count += 1
                                except Exception:
                                    failed_count += 1
                        except FutureTimeoutError:
                            logging.warning(f"번역 타임아웃: {symbol} - 완료된 번역만 사용")
                        
                        for future in future_to_index:
                            if future not in completed_futures:
                                try:
                                    future.cancel()
                                except:
                                    pass
                
                for i in range(max_translate, len(all_news)):
                    all_news[i]['title_ko'] = all_news[i].get('title', '')
                    all_news[i]['title_original'] = all_news[i].get('title', '')
                    all_news[i]['description_ko'] = all_news[i].get('description', '')
                    all_news[i]['description_original'] = all_news[i].get('description', '')
                
                translate_time = time.time() - translate_start
                logging.info(f"번역 완료: {symbol} - {translated_count}개 번역 성공, {failed_count}개 실패 (소요 시간: {translate_time:.2f}초)")
        else:
            for news in all_news:
                news['title_ko'] = news.get('title', '')
                news['title_original'] = news.get('title', '')
                news['description_ko'] = news.get('description', '')
                news['description_original'] = news.get('description', '')
        
        all_news = sorted(all_news, key=lambda x: x.get('published_at', ''), reverse=True)
        
        self.cache[cache_key] = (all_news, datetime.now())
        
        total_time = time.time() - start_time
        logging.info(f"{symbol} 뉴스 수집 완료: {len(all_news)}개 (총 소요 시간: {total_time:.2f}초)")
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
                prefix = "E2K: "
                if len(text) > 200:
                    chunks = [text[i:i+200] for i in range(0, len(text), 200)]
                    translated_chunks = []
                    for chunk in chunks:
                        if self._is_korean_text(chunk):
                            translated_chunks.append(chunk)
                        else:
                            result = self.hf_translator(prefix + chunk)
                            translated_chunks.append(result[0]['translation_text'])
                    return ' '.join(translated_chunks)
                else:
                    if self._is_korean_text(text):
                        return text
                    result = self.hf_translator(prefix + text)
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
        translated_news = news.copy()
        
        title = news.get('title', '')
        description = news.get('description', '')
        
        if title:
            translated_news['title_original'] = title
            if self._is_korean_text(title):
                translated_news['title_ko'] = title
            elif translate_to_korean and (self.hf_translator or self.translator):
                try:
                    translated_title = self.translate_text(title, 'ko')
                    translated_news['title_ko'] = translated_title if translated_title and translated_title != title else title
                except Exception as e:
                    logging.warning(f"제목 번역 실패: {str(e)}")
                    translated_news['title_ko'] = title
            else:
                translated_news['title_ko'] = title
        
        if description:
            translated_news['description_original'] = description
            if self._is_korean_text(description):
                translated_news['description_ko'] = description
            elif translate_to_korean and (self.hf_translator or self.translator):
                try:
                    translated_desc = self.translate_text(description, 'ko')
                    translated_news['description_ko'] = translated_desc if translated_desc and translated_desc != description else description
                except Exception as e:
                    logging.warning(f"설명 번역 실패: {str(e)}")
                    translated_news['description_ko'] = description
            else:
                translated_news['description_ko'] = description
        
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

