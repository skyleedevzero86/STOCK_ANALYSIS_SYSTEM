from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path, Request, Depends, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from typing import Protocol, TypedDict, List, Dict, Optional, Union, Any
import asyncio
import json
import os
import smtplib
import pandas as pd
from datetime import datetime, timedelta
import uvicorn
import time
from contextlib import asynccontextmanager

from api_common import (
    StockDataResponse,
    AdvancedAnalysisResponse,
    EnhancedErrorResponse,
    NewsResponse,
    PerformanceMetrics,
    ConnectionManager,
    create_cors_middleware_config,
    TechnicalAnalysisResponse,
    ErrorResponse,
    EmailNotificationRequest,
    EmailNotificationResponse,
    SmsNotificationRequest,
    SmsNotificationResponse,
    format_timestamp,
    safe_float
)
from utils.data_formatter import DataFormatter
from utils.retry_handler import RetryHandler
from utils.notification_logger import NotificationLogger
from exceptions import (
    StockAnalysisBaseException,
    StockDataCollectionError,
    StockNotFoundError,
    InvalidSymbolError,
    StockAnalysisError,
    NetworkError,
    TimeoutError,
    RateLimitError,
    HTTPError,
    ExternalServiceError,
    DatabaseError,
    DatabaseConnectionError,
    NotificationError,
    EmailNotificationError,
    SMSNotificationError,
    ConfigurationError,
    WebSocketError,
    WebSocketConnectionError
)

from data_collectors.performance_optimized_collector import PerformanceOptimizedCollector
from data_collectors.stock_data_collector import StockDataCollector
from data_collectors.news_collector import NewsCollector
from analysis_engine.advanced_analyzer import AdvancedTechnicalAnalyzer
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService
from security.security_manager import SecurityManager, SecurityConfig
from error_handling.error_manager import ErrorManager, ErrorSeverity, ErrorCategory, error_handler, ErrorContext
from config.settings import get_settings
from config.logging_config import get_logger, setup_logging
import re

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False
    logger = get_logger(__name__, "stock_analysis.log")
    logger.debug("pymysql 모듈이 설치되지 않았습니다. 이메일 발송 이력 저장 기능이 비활성화됩니다.")

settings = get_settings()

setup_logging(log_file="stock_analysis.log")
logger = get_logger(__name__, "stock_analysis.log")
security = HTTPBearer()

class RealtimeDataDict(TypedDict):
    symbol: str
    price: float
    volume: int
    change: float
    change_percent: float
    timestamp: datetime
    confidence_score: float

class AnalysisDataDict(TypedDict):
    symbol: str
    currentPrice: float
    volume: int
    changePercent: float
    trend: str
    trendStrength: float
    marketRegime: str
    signals: Dict[str, Any]
    patterns: List[Dict[str, Any]]
    supportResistance: Dict[str, Any]
    fibonacciLevels: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    riskScore: float
    confidence: float
    timestamp: str

class DataCollectorProtocol(Protocol):
    async def get_realtime_data_async(self, symbol: str) -> Dict[str, Any]:
        pass
    
    async def get_historical_data_async(self, symbol: str, period: str) -> pd.DataFrame:
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        pass
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        pass

class AnalyzerProtocol(Protocol):
    def calculate_all_advanced_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        pass
    
    def calculate_market_regime(self, data: pd.DataFrame) -> Dict[str, Any]:
        pass
    
    def detect_chart_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        pass
    
    def calculate_support_resistance(self, data: pd.DataFrame) -> Dict[str, Any]:
        pass
    
    def calculate_fibonacci_levels(self, data: pd.DataFrame) -> Dict[str, Any]:
        pass
    
    def detect_anomalies_ml(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        pass
    
    def calculate_advanced_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        pass

class NewsCollectorProtocol(Protocol):
    def get_stock_news(self, symbol: str, include_korean: bool, auto_translate: bool) -> List[Dict[str, Any]]:
        pass
    
    def search_news(self, query: str, language: str, max_results: int) -> List[Dict[str, Any]]:
        pass
    
    def get_multiple_stock_news(self, symbols: List[str], include_korean: bool) -> Dict[str, List[Dict[str, Any]]]:
        pass
    
    def get_news_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("애플리케이션 시작: 서비스 초기화 중", service="api_server")
    try:
        app.state.data_collector = PerformanceOptimizedCollector(
            symbols=settings.ANALYSIS_SYMBOLS,
            max_workers=10,
            cache_ttl=300
        )
        
        app.state.enhanced_collector = StockDataCollector(
            settings.ANALYSIS_SYMBOLS,
            use_mock_data=settings.USE_MOCK_DATA,
            use_alpha_vantage=True,
            fallback_to_mock=settings.FALLBACK_TO_MOCK
        )
        
        app.state.analyzer = AdvancedTechnicalAnalyzer()
        app.state.basic_analyzer = TechnicalAnalyzer()
        
        email_config = {
            'smtp_server': settings.EMAIL_SMTP_SERVER,
            'smtp_port': settings.EMAIL_SMTP_PORT,
            'user': settings.EMAIL_USER,
            'password': settings.EMAIL_PASSWORD
        }
        solapi_config = {
            'api_key': settings.SOLAPI_API_KEY,
            'api_secret': settings.SOLAPI_API_SECRET
        }
        app.state.notification_service = NotificationService(
            email_config=email_config,
            slack_webhook=settings.SLACK_WEBHOOK_URL,
            solapi_config=solapi_config
        )
        
        security_config = SecurityConfig(
            jwt_secret=settings.JWT_SECRET,
            jwt_expiry=settings.JWT_EXPIRY,
            max_login_attempts=settings.MAX_LOGIN_ATTEMPTS,
            lockout_duration=settings.LOCKOUT_DURATION
        )
        app.state.security_manager = SecurityManager(security_config)
        
        app.state.error_manager = ErrorManager()
        
        async with app.state.data_collector:
            yield
        
    except ConfigurationError:
        raise
    except Exception as e:
        logger.error("애플리케이션 시작 오류", exception=e, service="api_server")
        raise ConfigurationError(
            f"애플리케이션 초기화 실패: {str(e)}",
            error_code="APP_INIT_FAILED",
            cause=e
        ) from e
    finally:
        logger.info("애플리케이션 종료: 정리 중")
        if hasattr(app.state, 'data_collector'):
            await app.state.data_collector.__aexit__(None, None, None)

app = FastAPI(
    title="Enhanced Stock Analysis API",
    version="2.0.0",
    description="고급 실시간 주식 데이터 수집 및 기술적 분석 API",
    contact={
        "name": "Stock Analysis Team",
        "email": "contact@stockanalysis.com"
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0"
    },
    lifespan=lifespan
)

cors_config = create_cors_middleware_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.stockanalysis.com"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

manager = ConnectionManager(enable_metadata=True)

class StockAnalysisAPI:
    def __init__(
        self,
        data_collector: DataCollectorProtocol,
        analyzer: AnalyzerProtocol,
        security_manager: SecurityManager,
        error_manager: ErrorManager,
        news_collector: NewsCollectorProtocol
    ) -> None:
        self.data_collector = data_collector
        self.analyzer = analyzer
        self.security_manager = security_manager
        self.error_manager = error_manager
        self.news_collector = news_collector
        
    async def _handle_realtime_data_error(self, e: Exception, symbol: str, context: ErrorContext, 
                                     max_retries: int, attempt: int) -> Optional[Dict[str, Any]]:
        if isinstance(e, HTTPException):
            raise
        elif isinstance(e, TimeoutError):
            if attempt < max_retries - 1:
                return None
            error_id = self.error_manager.log_error(
                ErrorSeverity.HIGH,
                ErrorCategory.DATA_COLLECTION,
                f"실시간 데이터 조회 타임아웃: {symbol} ({max_retries}회 시도 후)",
                e,
                context
            )
            logger.error("실시간 데이터 조회 타임아웃", symbol=symbol, error_id=error_id, retry_count=attempt+1)
            raise HTTPException(
                status_code=504,
                detail=f"데이터 조회 시간 초과. 오류 ID: {error_id}"
            ) from e
        elif isinstance(e, (ConnectionError, NetworkError)):
            if attempt < max_retries - 1:
                return None
            error_id = self.error_manager.log_error(
                ErrorSeverity.HIGH,
                ErrorCategory.NETWORK,
                f"네트워크 오류: {symbol} ({max_retries}회 시도 후)",
                e,
                context
            )
            logger.error("네트워크 오류", symbol=symbol, error_id=error_id, retry_count=attempt+1)
            raise HTTPException(
                status_code=503,
                detail=f"네트워크 오류. 오류 ID: {error_id}"
            ) from e
        elif isinstance(e, StockDataCollectionError):
            if attempt < max_retries - 1:
                return None
            error_id = self.error_manager.log_error(
                ErrorSeverity.HIGH,
                ErrorCategory.DATA_COLLECTION,
                f"데이터 수집 오류: {symbol} ({max_retries}회 시도 후) - {str(e)}",
                e,
                context
            )
            logger.error("데이터 수집 오류", symbol=symbol, error_id=error_id, retry_count=attempt+1, exception=e)
            fallback_data = await self._get_fallback_data(symbol)
            if fallback_data:
                logger.warning("대체 데이터 사용 중", symbol=symbol)
                return fallback_data
            raise HTTPException(
                status_code=500,
                detail=f"데이터 수집 오류. 오류 ID: {error_id}"
            ) from e
        else:
            if attempt < max_retries - 1:
                return None
            error_id = self.error_manager.log_error(
                ErrorSeverity.HIGH,
                ErrorCategory.DATA_COLLECTION,
                f"실시간 데이터 조회 오류: {symbol} ({max_retries}회 시도 후) - {str(e)}",
                e,
                context
            )
            logger.error("실시간 데이터 조회 오류", symbol=symbol, error_id=error_id, retry_count=attempt+1, exception=e)
            fallback_data = await self._get_fallback_data(symbol)
            if fallback_data:
                logger.warning("대체 데이터 사용 중", symbol=symbol)
                return fallback_data
            raise StockDataCollectionError(
                f"실시간 데이터 조회 실패: {symbol}",
                error_code="DATA_FETCH_FAILED",
                cause=e
            ) from e
    
    async def get_realtime_data_enhanced(self, symbol: str) -> Dict[str, Any]:
        context = ErrorContext(
            endpoint=f"/api/realtime/{symbol}",
            parameters={'symbol': symbol}
        )
        
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                context.retry_count = attempt
                
                data = await self.data_collector.get_realtime_data_async(symbol)
                
                if not data or data.get('price', 0) <= 0:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    
                    error_id = self.error_manager.log_error(
                        ErrorSeverity.MEDIUM,
                        ErrorCategory.DATA_COLLECTION,
                        f"종목 데이터를 찾을 수 없습니다: {symbol} ({max_retries}회 시도 후)",
                        None,
                        context
                    )
                    raise HTTPException(
                        status_code=404, 
                        detail=f"종목 데이터를 찾을 수 없습니다: {symbol}. 오류 ID: {error_id}"
                    )
                
                response_time = time.time() - start_time
                confidence_score = data.get('confidence_score', 0.95)
                confidence_score = min(1.0, max(0.0, confidence_score - (response_time / 5.0)))
                
                if context.retry_count > 0:
                    context.recovery_attempted = True
                    self.error_manager.log_error(
                        ErrorSeverity.LOW,
                        ErrorCategory.DATA_COLLECTION,
                        f"데이터 복구 성공: {symbol} ({context.retry_count}회 재시도 후)",
                        None,
                        context
                    )
                
                return DataFormatter.format_realtime_response(data, confidence_score)
                
            except Exception as e:
                result = await self._handle_realtime_data_error(e, symbol, context, max_retries, attempt)
                if result is not None:
                    return result
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
    
    async def _get_fallback_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            from data_collectors.stock_data_collector import StockDataCollector
            fallback_collector = StockDataCollector([symbol], use_mock_data=True, fallback_to_mock=True)
            fallback_data = fallback_collector.get_realtime_data(symbol)
            
            if fallback_data and fallback_data.get('price', 0) > 0:
                return DataFormatter.format_fallback_data(fallback_data)
        except (StockDataCollectionError, Exception) as e:
            logger.error("대체 데이터 조회 실패", symbol=symbol, exception=e)
        
        return None
    
    async def _fetch_historical_data_with_retry(self, symbol: str, context: ErrorContext) -> pd.DataFrame:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                historical_data = await self.data_collector.get_historical_data_async(symbol, "3mo")
                if not historical_data.empty:
                    return historical_data
            except (TimeoutError, ConnectionError, NetworkError) as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                error_id = self.error_manager.log_error(
                    ErrorSeverity.MEDIUM,
                    ErrorCategory.DATA_COLLECTION,
                    f"과거 데이터 조회 네트워크 오류: {symbol} ({max_retries}회 시도 후)",
                    e,
                    context
                )
                historical_data = await self._get_fallback_historical_data(symbol)
                if historical_data.empty:
                    raise HTTPException(
                        status_code=503,
                        detail=f"과거 데이터 조회 실패: {symbol}. 오류 ID: {error_id}"
                    ) from e
                return historical_data
            except StockDataCollectionError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                error_id = self.error_manager.log_error(
                    ErrorSeverity.MEDIUM,
                    ErrorCategory.DATA_COLLECTION,
                    f"과거 데이터 조회 실패: {symbol} ({max_retries}회 시도 후) - {str(e)}",
                    e,
                    context
                )
                historical_data = await self._get_fallback_historical_data(symbol)
                if historical_data.empty:
                    raise HTTPException(
                        status_code=404,
                        detail=f"과거 데이터를 찾을 수 없습니다: {symbol}. 오류 ID: {error_id}"
                    ) from e
                return historical_data
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                error_id = self.error_manager.log_error(
                    ErrorSeverity.MEDIUM,
                    ErrorCategory.DATA_COLLECTION,
                    f"과거 데이터 조회 실패: {symbol} ({max_retries}회 시도 후) - {str(e)}",
                    e,
                    context
                )
                historical_data = await self._get_fallback_historical_data(symbol)
                if historical_data.empty:
                    raise StockDataCollectionError(
                        f"과거 데이터를 찾을 수 없습니다: {symbol}",
                        error_code="HISTORICAL_DATA_NOT_FOUND",
                        cause=e
                    ) from e
                return historical_data
        return pd.DataFrame()
    
    def _calculate_indicators_safe(self, data: pd.DataFrame, symbol: str, context: ErrorContext) -> pd.DataFrame:
        try:
            return self.analyzer.calculate_all_advanced_indicators(data)
        except (ValueError, TypeError, StockAnalysisError) as e:
            error_id = self.error_manager.log_error(
                ErrorSeverity.MEDIUM,
                ErrorCategory.ANALYSIS,
                f"지표 계산 오류: {symbol} - {str(e)}",
                e,
                context
            )
            return data
        except Exception as e:
            error_id = self.error_manager.log_error(
                ErrorSeverity.MEDIUM,
                ErrorCategory.ANALYSIS,
                f"지표 계산 예상치 못한 오류: {symbol} - {str(e)}",
                e,
                context
            )
            return data
    
    def _calculate_analysis_components_safe(self, analyzed_data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        components = {
            'market_regime': {'regime': 'unknown', 'confidence': 0.0},
            'patterns': [],
            'support_resistance': {'support': [], 'resistance': []},
            'fibonacci_levels': {},
            'anomalies': [],
            'signals': {'signal': 'hold', 'confidence': 0.0, 'signals': []}
        }
        
        try:
            components['market_regime'] = self.analyzer.calculate_market_regime(analyzed_data)
        except Exception as e:
            logger.warning("시장 상황 계산 오류", symbol=symbol, exception=e)
        
        try:
            components['patterns'] = self.analyzer.detect_chart_patterns(analyzed_data)
        except Exception as e:
            logger.warning("패턴 감지 오류", symbol=symbol, exception=e)
        
        try:
            components['support_resistance'] = self.analyzer.calculate_support_resistance(analyzed_data)
        except Exception as e:
            logger.warning("지지/저항선 계산 오류", symbol=symbol, exception=e)
        
        try:
            components['fibonacci_levels'] = self.analyzer.calculate_fibonacci_levels(analyzed_data)
        except Exception as e:
            logger.warning("피보나치 레벨 계산 오류", symbol=symbol, exception=e)
        
        try:
            components['anomalies'] = self.analyzer.detect_anomalies_ml(analyzed_data)
        except Exception as e:
            logger.warning("이상 패턴 감지 오류", symbol=symbol, exception=e)
        
        try:
            components['signals'] = self.analyzer.calculate_advanced_signals(analyzed_data)
        except Exception as e:
            logger.warning("신호 계산 오류", symbol=symbol, exception=e)
        
        return components
    
    async def get_advanced_analysis(self, symbol: str) -> Dict[str, Any]:
        context = ErrorContext(
            endpoint=f"/api/analysis/{symbol}",
            parameters={'symbol': symbol}
        )
        
        try:
            realtime_data = await self.get_realtime_data_enhanced(symbol)
            historical_data = await self._fetch_historical_data_with_retry(symbol, context)
            analyzed_data = self._calculate_indicators_safe(historical_data, symbol, context)
            components = self._calculate_analysis_components_safe(analyzed_data, symbol)
            
            risk_score = self._calculate_risk_score(analyzed_data, components['anomalies'])
            confidence = self._calculate_analysis_confidence(analyzed_data, components['market_regime'])
            
            return {
                'symbol': symbol,
                'currentPrice': realtime_data['currentPrice'],
                'volume': realtime_data.get('volume', 0),
                'changePercent': realtime_data.get('changePercent', 0),
                'trend': components['signals'].get('signal', 'hold'),
                'trendStrength': components['signals'].get('confidence', 0.0),
                'marketRegime': components['market_regime'].get('regime', 'unknown'),
                'signals': components['signals'],
                'patterns': components['patterns'],
                'supportResistance': components['support_resistance'],
                'fibonacciLevels': components['fibonacci_levels'],
                'anomalies': [
                    {
                        'type': anomaly.get('type', 'unknown'),
                        'severity': anomaly.get('severity', 'low'),
                        'message': anomaly.get('message', f"이상 패턴 감지: {anomaly.get('type', 'unknown')}"),
                        'timestamp': datetime.now().isoformat()
                    } for anomaly in components['anomalies']
                ],
                'riskScore': risk_score,
                'confidence': confidence,
                'timestamp': datetime.now()
            }
            
        except HTTPException:
            raise
        except StockAnalysisError as e:
            error_id = self.error_manager.log_error(
                ErrorSeverity.HIGH,
                ErrorCategory.ANALYSIS,
                f"고급 분석 오류: {symbol} - {str(e)}",
                e,
                context
            )
            logger.error("고급 분석 오류", symbol=symbol, error_id=error_id, exception=e)
            raise HTTPException(
                status_code=500,
                detail=f"분석 오류. 오류 ID: {error_id}"
            ) from e
        except Exception as e:
            error_id = self.error_manager.log_error(
                ErrorSeverity.HIGH,
                ErrorCategory.ANALYSIS,
                f"고급 분석 예상치 못한 오류: {symbol} - {str(e)}",
                e,
                context
            )
            logger.error("고급 분석 오류", symbol=symbol, error_id=error_id, exception=e)
            raise StockAnalysisError(
                f"고급 분석 실패: {symbol}",
                error_code="ANALYSIS_FAILED",
                cause=e
            ) from e
    
    async def _get_fallback_historical_data(self, symbol: str) -> pd.DataFrame:
        try:
            from data_collectors.stock_data_collector import StockDataCollector
            fallback_collector = StockDataCollector([symbol], use_mock_data=True, fallback_to_mock=True)
            return fallback_collector.get_historical_data(symbol, "3mo")
        except StockDataCollectionError as e:
            logger.error("대체 과거 데이터 조회 실패", symbol=symbol, exception=e)
            return pd.DataFrame()
        except Exception as e:
            logger.error("대체 과거 데이터 조회 실패", symbol=symbol, exception=e)
            return pd.DataFrame()
    
    def _calculate_risk_score(self, data: pd.DataFrame, anomalies: List[Dict[str, Any]]) -> float:
        base_risk = 0.1
        
        if len(anomalies) > 0:
            base_risk += min(0.4, len(anomalies) * 0.1)
        
        if 'close' in data.columns and len(data) > 1:
            volatility = data['close'].pct_change().std()
            if pd.notna(volatility):
                base_risk += min(0.3, float(volatility) * 10)
        
        return min(1.0, base_risk)
    
    def _calculate_analysis_confidence(self, data: pd.DataFrame, market_regime: Dict[str, Any]) -> float:
        base_confidence = 0.5
        
        if market_regime.get('confidence', 0) > 0.7:
            base_confidence += 0.2
        
        if len(data) > 100:
            base_confidence += 0.2
        
        if 'volume' in data.columns and len(data) > 0:
            avg_volume = data['volume'].mean()
            if pd.notna(avg_volume) and avg_volume > 1000000:
                base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    async def get_batch_analysis(self, symbols: List[str]) -> List[Dict[str, Any]]:
        try:
            tasks = [self.get_advanced_analysis(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error("종목 분석 오류", symbol=symbols[i], error=str(result))
                    continue
                if result:
                    valid_results.append(result)
            
            return valid_results
            
        except StockAnalysisError as e:
            error_id = self.error_manager.log_error(
                ErrorSeverity.MEDIUM,
                ErrorCategory.ANALYSIS,
                f"배치 분석 오류: {str(e)}",
                e
            )
            logger.error("배치 분석 오류", error_id=error_id, exception=e)
            raise HTTPException(
                status_code=500,
                detail=f"배치 분석 오류. 오류 ID: {error_id}"
            ) from e
        except Exception as e:
            error_id = self.error_manager.log_error(
                ErrorSeverity.MEDIUM,
                ErrorCategory.ANALYSIS,
                f"배치 분석 예상치 못한 오류: {str(e)}",
                e
            )
            logger.error("배치 분석 오류", error_id=error_id, exception=e)
            raise StockAnalysisError(
                "배치 분석 실패",
                error_code="BATCH_ANALYSIS_FAILED",
                cause=e
            ) from e
    
    def _load_historical_data(self, symbol: str):
        import numpy as np
        dates = pd.date_range(start=datetime.now() - pd.Timedelta(days=60), end=datetime.now(), freq='D')
        np.random.seed(hash(symbol) % 2**32)
        
        base_price = 100 + hash(symbol) % 200
        price_changes = np.random.randn(len(dates)) * 2
        prices = base_price + np.cumsum(price_changes)
        
        return pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })
    
    async def get_basic_analysis(self, symbol: str, basic_analyzer: TechnicalAnalyzer, 
                                 enhanced_collector: StockDataCollector) -> Dict[str, Any]:
        try:
            
            realtime_data = enhanced_collector.get_realtime_data(symbol)
            if not realtime_data:
                raise HTTPException(status_code=404, detail=f"종목 데이터를 찾을 수 없습니다: {symbol}")
            
            historical_data = self._load_historical_data(symbol)
            
            if historical_data.empty:
                raise HTTPException(status_code=404, detail=f"과거 데이터를 찾을 수 없습니다: {symbol}")
            
            analyzed_data = basic_analyzer.calculate_all_indicators(historical_data)
            trend_analysis = basic_analyzer.analyze_trend(analyzed_data)
            anomalies = basic_analyzer.detect_anomalies(analyzed_data, symbol)
            signals = basic_analyzer.generate_signals(analyzed_data, symbol)
            
            timestamp = format_timestamp(realtime_data.get('timestamp'))
            
            return {
                'symbol': symbol,
                'currentPrice': realtime_data['price'],
                'volume': realtime_data.get('volume', 0),
                'changePercent': realtime_data.get('change_percent', 0),
                'trend': trend_analysis['trend'],
                'trendStrength': trend_analysis['strength'],
                'signals': {
                    'signal': signals['signal'],
                    'confidence': signals['confidence'],
                    'rsi': analyzed_data['rsi_14'].iloc[-1] if 'rsi_14' in analyzed_data.columns and not analyzed_data['rsi_14'].isna().iloc[-1] else None,
                    'macd': analyzed_data['macd'].iloc[-1] if 'macd' in analyzed_data.columns and not analyzed_data['macd'].isna().iloc[-1] else None,
                    'macdSignal': analyzed_data['macd_signal'].iloc[-1] if 'macd_signal' in analyzed_data.columns and not analyzed_data['macd_signal'].isna().iloc[-1] else None
                },
                'anomalies': [
                    {
                        'type': anomaly['type'],
                        'severity': anomaly['severity'],
                        'message': anomaly['message'],
                        'timestamp': datetime.now()
                    } for anomaly in anomalies
                ],
                'timestamp': timestamp
            }
        except HTTPException:
            raise
        except StockAnalysisError as e:
            logger.error("분석 오류", symbol=symbol, exception=e)
            raise HTTPException(status_code=500, detail=f"분석 오류: {str(e)}") from e
        except Exception as e:
            logger.error("분석 예상치 못한 오류", symbol=symbol, exception=e)
            raise StockAnalysisError(
                f"분석 실패: {symbol}",
                error_code="BASIC_ANALYSIS_FAILED",
                cause=e
            ) from e
    
    async def get_all_symbols_analysis(self, basic_analyzer: Optional[TechnicalAnalyzer] = None,
                                       enhanced_collector: Optional[StockDataCollector] = None) -> List[Dict[str, Any]]:
        try:
            import asyncio
            results = []
            symbols_count = len(settings.ANALYSIS_SYMBOLS)
            logger.info(f"전체 종목 분석 시작: {symbols_count}개 종목")
            
            for idx, symbol in enumerate(settings.ANALYSIS_SYMBOLS):
                try:
                    logger.info(f"종목 분석 중 ({idx+1}/{symbols_count}): {symbol}")
                    if basic_analyzer and enhanced_collector:
                        analysis = await self.get_basic_analysis(symbol, basic_analyzer, enhanced_collector)
                    else:
                        analysis = await self.get_advanced_analysis(symbol)
                    
                    if analysis:
                        results.append(analysis)
                        logger.info(f"종목 분석 성공: {symbol}")
                    else:
                        logger.warning(f"종목 분석 결과가 None: {symbol}")
                    
                    if idx < len(settings.ANALYSIS_SYMBOLS) - 1:
                        await asyncio.sleep(0.5)
                        
                except (StockAnalysisError, StockDataCollectionError) as e:
                    logger.error("종목 분석 오류", symbol=symbol, exception=e)
                    if idx < len(settings.ANALYSIS_SYMBOLS) - 1:
                        await asyncio.sleep(0.3)
                    continue
                except Exception as e:
                    logger.error("종목 분석 예상치 못한 오류", symbol=symbol, exception=e, exc_info=True)
                    if idx < len(settings.ANALYSIS_SYMBOLS) - 1:
                        await asyncio.sleep(0.3)
                    continue
            
            logger.info(f"전체 종목 분석 완료: {len(results)}/{symbols_count}개 성공")
            return results
        except StockAnalysisError as e:
            logger.error("전체 종목 분석 오류", exception=e)
            raise HTTPException(status_code=500, detail=f"전체 종목 분석 오류: {str(e)}") from e
        except Exception as e:
            logger.error("전체 종목 분석 예상치 못한 오류", exception=e)
            raise StockAnalysisError(
                "전체 종목 분석 실패",
                error_code="ALL_SYMBOLS_ANALYSIS_FAILED",
                cause=e
            ) from e
    
    async def get_historical_data(self, symbol: str, days: int, basic_analyzer: TechnicalAnalyzer) -> Dict[str, Any]:
        try:
            historical_data = self._load_historical_data(symbol)
            analyzed_data = basic_analyzer.calculate_all_indicators(historical_data)
            
            chart_data = []
            for i, row in analyzed_data.iterrows():
                chart_data.append({
                    'date': row['date'].isoformat(),
                    'close': safe_float(row['close'], 0.0),
                    'volume': int(row['volume']) if not pd.isna(row['volume']) else 0,
                    'rsi': safe_float(row.get('rsi')) if 'rsi' in row else None,
                    'macd': safe_float(row.get('macd')) if 'macd' in row else None,
                    'bb_upper': safe_float(row.get('bb_upper')) if 'bb_upper' in row else None,
                    'bb_lower': safe_float(row.get('bb_lower')) if 'bb_lower' in row else None,
                    'sma_20': safe_float(row.get('sma_20')) if 'sma_20' in row else None
                })
            
            return {
                'symbol': symbol,
                'data': chart_data,
                'period': days
            }
        except (ValueError, TypeError, StockAnalysisError) as e:
            logger.error("과거 데이터 조회 오류", symbol=symbol, exception=e)
            raise HTTPException(status_code=500, detail=f"과거 데이터 조회 오류: {str(e)}") from e
        except Exception as e:
            logger.error("과거 데이터 조회 예상치 못한 오류", symbol=symbol, exception=e)
            raise StockAnalysisError(
                f"과거 데이터 조회 실패: {symbol}",
                error_code="HISTORICAL_DATA_FETCH_FAILED",
                cause=e
            ) from e

def get_stock_api(request: Request) -> StockAnalysisAPI:
    if not hasattr(request.app.state, 'data_collector'):
        raise HTTPException(status_code=503, detail="서비스 초기화 중입니다")
    return StockAnalysisAPI(
        data_collector=request.app.state.data_collector,
        analyzer=request.app.state.analyzer,
        security_manager=request.app.state.security_manager,
        error_manager=request.app.state.error_manager,
        news_collector=NewsCollector()
    )

def get_enhanced_collector(request: Request) -> StockDataCollector:
    if not hasattr(request.app.state, 'enhanced_collector'):
        raise HTTPException(status_code=503, detail="서비스 초기화 중입니다")
    return request.app.state.enhanced_collector

def get_basic_analyzer(request: Request) -> TechnicalAnalyzer:
    if not hasattr(request.app.state, 'basic_analyzer'):
        raise HTTPException(status_code=503, detail="서비스 초기화 중입니다")
    return request.app.state.basic_analyzer

def get_notification_service(request: Request) -> NotificationService:
    if not hasattr(request.app.state, 'notification_service'):
        raise HTTPException(status_code=503, detail="서비스 초기화 중입니다")
    return request.app.state.notification_service

@app.get("/", 
         summary="API 서버 정보",
         description="Enhanced Stock Analysis API 서버의 기본 정보를 반환합니다.")
async def root() -> Dict[str, Any]:
    return {
        "message": "Enhanced Stock Analysis API Server", 
        "version": "2.0.0",
        "features": [
            "고급 기술적 분석",
            "실시간 데이터 스트리밍",
            "성능 최적화",
            "향상된 보안",
            "종합적인 오류 처리"
        ]
    }

@app.get("/api/health",
         summary="헬스 체크",
         description="API 서버의 상태를 확인합니다.")
async def health_check(request: Request) -> Dict[str, Any]:
    try:
        if not hasattr(request.app.state, 'data_collector'):
            return {
                "status": "initializing",
                "timestamp": datetime.now().isoformat()
            }
        
        api = get_stock_api(request)
        health_data = await api.data_collector.health_check()
        performance_metrics = api.data_collector.get_performance_metrics()
        
        return {
            "status": health_data.get('status', 'healthy'),
            "timestamp": datetime.now().isoformat(),
            "performance": performance_metrics,
            "connections": manager.get_connection_stats(),
            "errors": api.error_manager.get_error_statistics(hours=1)
        }
    except (NetworkError, DatabaseConnectionError) as e:
        logger.error("헬스 체크 실패", exception=e)
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("헬스 체크 예상치 못한 오류", exception=e)
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/performance",
         summary="성능 메트릭",
         description="API 서버의 성능 지표를 조회합니다.",
         response_model=PerformanceMetrics)
async def get_performance_metrics(api: StockAnalysisAPI = Depends(get_stock_api)) -> PerformanceMetrics:
    metrics = api.data_collector.get_performance_metrics()
    return PerformanceMetrics(**metrics)

@app.get("/api/realtime/{symbol}",
         summary="실시간 주가 데이터 (향상된)",
         description="특정 종목의 실시간 주가 정보를 조회합니다.",
         response_model=StockDataResponse,
         responses={
             200: {"description": "성공적으로 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": EnhancedErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": EnhancedErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def get_realtime_data(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> StockDataResponse:
    result = await api.get_realtime_data_enhanced(symbol)
    return StockDataResponse(**result)

@app.get("/api/analysis/advanced/{symbol}",
         summary="고급 기술적 분석 결과",
         description="특정 종목의 고급 기술적 분석 결과를 조회합니다.",
         response_model=AdvancedAnalysisResponse,
         responses={
             200: {"description": "성공적으로 분석 결과를 조회했습니다."},
             404: {"description": "해당 종목의 분석 데이터를 찾을 수 없습니다.", "model": EnhancedErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": EnhancedErrorResponse}
         })
@error_handler(ErrorSeverity.HIGH, ErrorCategory.ANALYSIS)
async def get_advanced_analysis(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> AdvancedAnalysisResponse:
    result = await api.get_advanced_analysis(symbol)
    return AdvancedAnalysisResponse(**result)

@app.get("/api/analysis/batch",
         summary="배치 분석",
         description="여러 종목의 분석을 동시에 수행합니다.",
         response_model=List[AdvancedAnalysisResponse])
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.ANALYSIS)
async def get_batch_analysis(
    symbols: str = Query(..., description="분석할 종목들 (쉼표로 구분)", example="AAPL,GOOGL,MSFT"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> List[AdvancedAnalysisResponse]:
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    if len(symbol_list) > 10:
        raise HTTPException(
            status_code=400,
            detail="배치 요청당 최대 10개 종목까지 허용됩니다"
        )
    
    results = await api.get_batch_analysis(symbol_list)
    return [AdvancedAnalysisResponse(**result) for result in results]

@app.get("/api/errors",
         summary="오류 통계",
         description="시스템 오류 통계를 조회합니다.")
async def get_error_statistics(
    hours: int = Query(24, description="조회할 시간 범위 (시간)", ge=1, le=168),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> Dict[str, Any]:
    return api.error_manager.get_error_statistics(hours=hours)

@app.get("/api/symbols",
         summary="분석 가능한 종목 목록",
         description="현재 분석 중인 주식 종목들의 목록을 반환합니다.",
         response_model=Dict[str, List[str]])
async def get_symbols():
    return {"symbols": settings.ANALYSIS_SYMBOLS}

@app.get("/api/analysis/all",
         summary="전체 종목 분석 결과",
         description="모든 분석 중인 종목의 기술적 분석 결과를 조회합니다.",
         response_model=List[TechnicalAnalysisResponse],
         responses={
             200: {"description": "성공적으로 모든 분석 결과를 조회했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_all_analysis(
    api: StockAnalysisAPI = Depends(get_stock_api),
    basic_analyzer: TechnicalAnalyzer = Depends(get_basic_analyzer),
    enhanced_collector: StockDataCollector = Depends(get_enhanced_collector)
):
    from pydantic import ValidationError
    from datetime import datetime as dt
    
    logger.info("전체 종목 분석 요청 시작")
    try:
        results = await api.get_all_symbols_analysis(basic_analyzer, enhanced_collector)
        logger.info(f"전체 종목 분석 완료: {len(results)}개 종목 분석됨")
    except Exception as e:
        logger.error("전체 종목 분석 중 오류 발생", exception=e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"전체 종목 분석 실패: {str(e)}") from e
    
    if not results:
        logger.warning("전체 종목 분석 결과가 비어있습니다")
        return []
    
    valid_results = []
    for result in results:
        try:
            if 'marketRegime' in result or 'market_regime' in result:
                signals_data = result.get('signals', {})
                if isinstance(signals_data, dict):
                    signals = {
                        'signal': signals_data.get('signal', 'hold'),
                        'confidence': signals_data.get('confidence', 0.0),
                        'rsi': signals_data.get('rsi'),
                        'macd': signals_data.get('macd'),
                        'macdSignal': signals_data.get('macd_signal') or signals_data.get('macdSignal')
                    }
                else:
                    signals = {
                        'signal': 'hold',
                        'confidence': 0.0,
                        'rsi': None,
                        'macd': None,
                        'macdSignal': None
                    }
                
                anomalies = []
                for anomaly in result.get('anomalies', []):
                    if isinstance(anomaly, dict):
                        timestamp = anomaly.get('timestamp')
                        if isinstance(timestamp, str):
                            try:
                                timestamp = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                            except:
                                timestamp = dt.now()
                        elif not isinstance(timestamp, dt):
                            timestamp = dt.now()
                        anomalies.append({
                            'type': anomaly.get('type', 'unknown'),
                            'severity': anomaly.get('severity', 'low'),
                            'message': anomaly.get('message', ''),
                            'timestamp': timestamp
                        })
                
                converted_result = {
                    'symbol': result.get('symbol'),
                    'currentPrice': result.get('currentPrice'),
                    'volume': result.get('volume', 0),
                    'changePercent': result.get('changePercent', 0),
                    'trend': result.get('trend', 'neutral'),
                    'trendStrength': result.get('trendStrength', 0.0),
                    'signals': signals,
                    'anomalies': anomalies,
                    'timestamp': result.get('timestamp', dt.now())
                }
                valid_results.append(TechnicalAnalysisResponse(**converted_result))
            else:
                valid_results.append(TechnicalAnalysisResponse(**result))
        except ValidationError as e:
            logger.error(
                f"Pydantic validation error for analysis result: {str(e)}",
                symbol=result.get('symbol'),
                errors=e.errors(),
                result_keys=list(result.keys()) if isinstance(result, dict) else None,
                result_type=type(result).__name__
            )
            continue
        except Exception as e:
            logger.error(
                f"분석 결과 변환 실패: {str(e)}",
                symbol=result.get('symbol') if isinstance(result, dict) else None,
                result_keys=list(result.keys()) if isinstance(result, dict) else None,
                result_type=type(result).__name__,
                exception=e,
                exc_info=True
            )
            continue
    
    logger.info(f"전체 종목 분석 응답: {len(valid_results)}개 유효한 결과 반환")
    if len(valid_results) == 0:
        logger.warning("유효한 분석 결과가 없습니다. 모든 결과가 검증에 실패했을 수 있습니다.")
    
    return valid_results

@app.get("/api/analysis/{symbol}",
         summary="기술적 분석 결과",
         description="특정 종목의 기술적 분석 결과를 조회합니다.",
         response_model=TechnicalAnalysisResponse,
         responses={
             200: {"description": "성공적으로 분석 결과를 조회했습니다."},
             404: {"description": "해당 종목의 분석 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_basic_analysis_endpoint(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    api: StockAnalysisAPI = Depends(get_stock_api),
    basic_analyzer: TechnicalAnalyzer = Depends(get_basic_analyzer),
    enhanced_collector: StockDataCollector = Depends(get_enhanced_collector)
):
    result = await api.get_basic_analysis(symbol, basic_analyzer, enhanced_collector)
    return TechnicalAnalysisResponse(**result)

@app.get("/api/historical/{symbol}",
         summary="과거 데이터",
         description="특정 종목의 과거 주가 데이터를 조회합니다.",
         responses={
             200: {"description": "성공적으로 과거 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 과거 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_historical_data(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    days: int = Query(30, description="조회할 일수", ge=1, le=365),
    api: StockAnalysisAPI = Depends(get_stock_api),
    basic_analyzer: TechnicalAnalyzer = Depends(get_basic_analyzer)
):
    return await api.get_historical_data(symbol, days, basic_analyzer)

@app.get("/api/alpha-vantage/search/{keywords}",
         summary="Alpha Vantage 종목 검색",
         description="Alpha Vantage API를 사용하여 종목을 검색합니다.",
         responses={
             200: {"description": "성공적으로 종목을 검색했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def search_symbols(
    keywords: str = Path(..., description="검색 키워드", example="Apple"),
    enhanced_collector: StockDataCollector = Depends(get_enhanced_collector)
):
    try:
        return enhanced_collector.search_alpha_vantage_symbols(keywords)
    except Exception as e:
        logger.error("종목 검색 오류", keywords=keywords, exception=e)
        raise HTTPException(status_code=500, detail=f"종목 검색 오류: {str(e)}")

@app.get("/api/alpha-vantage/intraday/{symbol}",
         summary="Alpha Vantage 분별 데이터",
         description="Alpha Vantage API를 사용하여 분별 주가 데이터를 조회합니다.",
         responses={
             200: {"description": "성공적으로 분별 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_alpha_vantage_intraday(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    interval: str = Query("5min", description="시간 간격", example="5min"),
    outputsize: str = Query("compact", description="출력 크기", example="compact"),
    enhanced_collector: StockDataCollector = Depends(get_enhanced_collector)
):
    try:
        data = enhanced_collector.get_alpha_vantage_intraday_data(symbol, interval, outputsize)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"분별 데이터를 찾을 수 없습니다: {symbol}")
        return data.to_dict('records')
    except HTTPException:
        raise
    except (TimeoutError, ConnectionError, NetworkError) as e:
        logger.error("분별 데이터 조회 네트워크 오류", symbol=symbol, exception=e)
        raise HTTPException(status_code=503, detail=f"분별 데이터 조회 네트워크 오류: {str(e)}") from e
    except StockDataCollectionError as e:
        logger.error("분별 데이터 조회 오류", symbol=symbol, exception=e)
        raise HTTPException(status_code=500, detail=f"분별 데이터 조회 오류: {str(e)}") from e
    except Exception as e:
        logger.error(f"분별 데이터 조회 예상치 못한 오류 ({symbol}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"분별 데이터 조회 오류: {str(e)}") from e

@app.get("/api/alpha-vantage/weekly/{symbol}",
         summary="Alpha Vantage 주별 데이터",
         description="Alpha Vantage API를 사용하여 주별 주가 데이터를 조회합니다.",
         responses={
             200: {"description": "성공적으로 주별 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_alpha_vantage_weekly(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    enhanced_collector: StockDataCollector = Depends(get_enhanced_collector)
):
    try:
        data = enhanced_collector.get_alpha_vantage_weekly_data(symbol)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"주별 데이터를 찾을 수 없습니다: {symbol}")
        return data.to_dict('records')
    except HTTPException:
        raise
    except (TimeoutError, ConnectionError, NetworkError) as e:
        logger.error("주별 데이터 조회 네트워크 오류", symbol=symbol, exception=e)
        raise HTTPException(status_code=503, detail=f"주별 데이터 조회 네트워크 오류: {str(e)}") from e
    except StockDataCollectionError as e:
        logger.error("주별 데이터 조회 오류", symbol=symbol, exception=e)
        raise HTTPException(status_code=500, detail=f"주별 데이터 조회 오류: {str(e)}") from e
    except Exception as e:
        logger.error(f"주별 데이터 조회 예상치 못한 오류 ({symbol}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"주별 데이터 조회 오류: {str(e)}") from e

@app.get("/api/alpha-vantage/monthly/{symbol}",
         summary="Alpha Vantage 월별 데이터",
         description="Alpha Vantage API를 사용하여 월별 주가 데이터를 조회합니다.",
         responses={
             200: {"description": "성공적으로 월별 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_alpha_vantage_monthly(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    enhanced_collector: StockDataCollector = Depends(get_enhanced_collector)
):
    try:
        data = enhanced_collector.get_alpha_vantage_monthly_data(symbol)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"월별 데이터를 찾을 수 없습니다: {symbol}")
        return data.to_dict('records')
    except HTTPException:
        raise
    except (TimeoutError, ConnectionError, NetworkError) as e:
        logger.error("월별 데이터 조회 네트워크 오류", symbol=symbol, exception=e)
        raise HTTPException(status_code=503, detail=f"월별 데이터 조회 네트워크 오류: {str(e)}") from e
    except StockDataCollectionError as e:
        logger.error("월별 데이터 조회 오류", symbol=symbol, exception=e)
        raise HTTPException(status_code=500, detail=f"월별 데이터 조회 오류: {str(e)}") from e
    except Exception as e:
        logger.error(f"월별 데이터 조회 예상치 못한 오류 ({symbol}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"월별 데이터 조회 오류: {str(e)}") from e

@app.post("/api/notifications/email",
         summary="이메일 발송",
         description="이메일을 발송합니다. 요청 본문 또는 쿼리 파라미터로 전달할 수 있습니다.",
         response_model=EmailNotificationResponse,
         responses={
             200: {"description": "이메일이 성공적으로 발송되었습니다."},
             400: {"description": "잘못된 요청입니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def send_email_notification(
    to_email: Optional[str] = Query(None, description="수신자 이메일"),
    subject: Optional[str] = Query(None, description="이메일 제목"),
    body: Optional[str] = Query(None, description="이메일 내용"),
    request_body: Optional[EmailNotificationRequest] = Body(None, description="요청 본문"),
    notification_service: NotificationService = Depends(get_notification_service)
):
    try:
        if request_body:
            to_email = request_body.to_email
            subject = request_body.subject
            body = request_body.body
        
        if not all([to_email, subject, body]):
            raise HTTPException(
                status_code=400,
                detail="to_email, subject, body는 필수입니다."
            )
        
        email_config = notification_service.email_config
        if not email_config:
            error_msg = "이메일 설정이 없습니다. 환경 변수 EMAIL_SMTP_SERVER, EMAIL_USER, EMAIL_PASSWORD를 확인하세요."
            logger.error(error_msg, to_email=to_email)
            NotificationLogger.log_notification(
                user_email=to_email,
                notification_type='email',
                message=f"[API발송] {subject}\n{body}",
                status="failed",
                error_message=error_msg
            )
            raise HTTPException(status_code=500, detail=error_msg)
        
        smtp_server = email_config.get('smtp_server')
        user = email_config.get('user')
        password = email_config.get('password')
        
        if not all([smtp_server, user, password]):
            missing = []
            if not smtp_server:
                missing.append("EMAIL_SMTP_SERVER")
            if not user:
                missing.append("EMAIL_USER")
            if not password:
                missing.append("EMAIL_PASSWORD")
            error_msg = f"이메일 설정이 완전하지 않습니다. 다음 환경 변수를 확인하세요: {', '.join(missing)}"
            logger.error(error_msg, to_email=to_email)
            NotificationLogger.log_notification(
                user_email=to_email,
                notification_type='email',
                message=f"[API발송] {subject}\n{body}",
                status="failed",
                error_message=error_msg
            )
            raise HTTPException(status_code=500, detail=error_msg)
        
        try:
            notification_service.send_email(
                to_email=to_email,
                subject=subject,
                body=body
            )
            
            NotificationLogger.log_notification(
                user_email=to_email,
                notification_type='email',
                message=f"[API발송] {subject}\n{body}",
                status="sent",
                error_message=None
            )
            
            return EmailNotificationResponse(
                success=True,
                message="이메일이 성공적으로 발송되었습니다."
            )
        except EmailNotificationError as e:
            error_msg = f"이메일 발송 실패: {str(e)}"
            logger.error("이메일 발송 오류", exception=e, to_email=to_email, smtp_server=smtp_server, error_code=getattr(e, 'error_code', None))
            NotificationLogger.log_notification(
                user_email=to_email,
                notification_type='email',
                message=f"[API발송] {subject}\n{body}",
                status="failed",
                error_message=error_msg
            )
            raise HTTPException(status_code=500, detail=error_msg) from e
    except HTTPException:
        raise
    except EmailNotificationError as e:
        error_msg = f"이메일 발송 오류: {str(e)}"
        logger.error("이메일 발송 오류 (외부 예외)", exception=e, to_email=to_email, error_code=getattr(e, 'error_code', None))
        NotificationLogger.log_notification(
            user_email=to_email,
            notification_type='email',
            message=f"[API발송] {subject}\n{body}",
            status="failed",
            error_message=error_msg
        )
        raise HTTPException(status_code=500, detail=error_msg) from e
    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        error_msg = f"이메일 발송 네트워크 오류: {str(e)}"
        logger.error("이메일 발송 네트워크 오류", exception=e, to_email=to_email, smtp_server=smtp_server)
        NotificationLogger.log_notification(
            user_email=to_email,
            notification_type='email',
            message=f"[API발송] {subject}\n{body}",
            status="failed",
            error_message=error_msg
        )
        raise HTTPException(status_code=503, detail=error_msg) from e
    except Exception as e:
        error_msg = f"이메일 발송 예상치 못한 오류: {str(e)}"
        logger.error("이메일 발송 예상치 못한 오류", exception=e, to_email=to_email, exc_info=True)
        NotificationLogger.log_notification(
            user_email=to_email,
            notification_type='email',
            message=f"[API발송] {subject}\n{body}",
            status="failed",
            error_message=error_msg
        )
        raise HTTPException(status_code=500, detail=error_msg) from e

@app.post("/api/notifications/sms",
         summary="문자 발송",
         description="문자(SMS/LMS)를 발송합니다. 요청 본문 또는 쿼리 파라미터로 전달할 수 있습니다.",
         response_model=SmsNotificationResponse,
         responses={
             200: {"description": "문자가 성공적으로 발송되었습니다."},
             400: {"description": "잘못된 요청입니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def send_sms_notification(
    from_phone: Optional[str] = Query(None, description="발신번호 (01012345678 형식)"),
    to_phone: Optional[str] = Query(None, description="수신번호 (01012345678 형식)"),
    message: Optional[str] = Query(None, description="메시지 내용"),
    request_body: Optional[SmsNotificationRequest] = Body(None, description="요청 본문"),
    notification_service: NotificationService = Depends(get_notification_service)
):
    try:
        if request_body:
            from_phone = request_body.from_phone
            to_phone = request_body.to_phone
            message = request_body.message
        
        if not to_phone or not message:
            raise HTTPException(
                status_code=400,
                detail="to_phone, message는 필수입니다."
            )
        
        if not from_phone:
            from_phone = settings.SOLAPI_FROM_PHONE
        
        if not from_phone:
            raise HTTPException(
                status_code=400,
                detail="발신번호가 설정되지 않았습니다. 환경 변수 SOLAPI_FROM_PHONE을 설정해주세요."
            )
        
        from_phone = from_phone.replace("-", "").replace(" ", "")
        to_phone = to_phone.replace("-", "").replace(" ", "")
        
        phone_regex = r'^010\d{8}$'
        if not re.match(phone_regex, from_phone):
            raise HTTPException(
                status_code=400,
                detail="발신번호 형식이 올바르지 않습니다. (01012345678 형식)"
            )
        if not re.match(phone_regex, to_phone):
            raise HTTPException(
                status_code=400,
                detail="수신번호 형식이 올바르지 않습니다. (01012345678 형식)"
            )
        success = notification_service.send_sms(
            from_phone=from_phone,
            to_phone=to_phone,
            message=message
        )
        
        NotificationLogger.log_notification(
            user_email=to_phone,
            notification_type='sms',
            message=f"[API발송] {message}",
            status="sent" if success else "failed",
            error_message=None if success else "문자 발송에 실패했습니다."
        )
        
        if success:
            return SmsNotificationResponse(
                success=True,
                message="문자가 성공적으로 발송되었습니다."
            )
        else:
            return SmsNotificationResponse(
                success=False,
                message="문자 발송에 실패했습니다."
            )
    except HTTPException:
        raise
    except SMSNotificationError as e:
        logger.error("문자 발송 오류", exception=e, to_phone=to_phone)
        raise HTTPException(status_code=500, detail=f"문자 발송 오류: {str(e)}") from e
    except (ConnectionError, TimeoutError, RateLimitError) as e:
        logger.error("문자 발송 네트워크 오류", exception=e, to_phone=to_phone)
        raise HTTPException(status_code=503, detail=f"문자 발송 네트워크 오류: {str(e)}") from e
    except Exception as e:
        logger.error("문자 발송 예상치 못한 오류", exception=e, to_phone=to_phone)
        raise SMSNotificationError(
            f"문자 발송 실패: {str(e)}",
            error_code="SMS_SEND_FAILED",
            cause=e
        ) from e

@app.get("/api/notifications/sms-config",
         summary="SMS 발신번호 조회",
         description="설정된 SMS 발신번호를 조회합니다.")
async def get_sms_config():
    try:
        from_phone = settings.SOLAPI_FROM_PHONE
        return {
            "fromPhone": from_phone
        }
    except ConfigurationError as e:
        logger.error("SMS 설정 조회 오류", exception=e)
        raise HTTPException(status_code=500, detail=f"SMS 설정 조회 오류: {str(e)}") from e
    except Exception as e:
        logger.error("SMS 설정 조회 예상치 못한 오류", exception=e)
        raise ConfigurationError(
            f"SMS 설정 조회 실패: {str(e)}",
            error_code="SMS_CONFIG_READ_FAILED",
            cause=e
        ) from e

@app.post("/api/notifications/realtime-email",
         summary="실시간 이메일 발송",
         description="Airflow 스케줄러를 거치지 않고 즉시 이메일을 발송합니다. 이벤트 발생 시 실시간으로 알림을 보낼 때 사용합니다.",
         response_model=EmailNotificationResponse,
         responses={
             200: {"description": "이메일이 성공적으로 발송되었습니다."},
             400: {"description": "잘못된 요청입니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def send_realtime_email(
    to_email: str = Query(..., description="수신자 이메일"),
    subject: str = Query(..., description="이메일 제목"),
    body: str = Query(..., description="이메일 내용"),
    notification_service: NotificationService = Depends(get_notification_service)
):
    try:
        logger.info("실시간 이메일 발송 요청", to_email=to_email, subject=subject)
        
        success = notification_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )
        
        NotificationLogger.log_notification(
            user_email=to_email,
            notification_type='email',
            message=f"[실시간발송] {subject}\n{body}",
            status="sent" if success else "failed",
            error_message=None if success else "이메일 발송에 실패했습니다."
        )
        
        if success:
            logger.info("실시간 이메일 발송 성공", to_email=to_email)
            return EmailNotificationResponse(
                success=True,
                message="이메일이 성공적으로 발송되었습니다."
            )
        else:
            logger.warning("실시간 이메일 발송 실패", to_email=to_email)
            return EmailNotificationResponse(
                success=False,
                message="이메일 발송에 실패했습니다."
            )
    except HTTPException:
        raise
    except EmailNotificationError as e:
        logger.error("실시간 이메일 발송 오류", exception=e, to_email=to_email)
        raise HTTPException(status_code=500, detail=f"이메일 발송 오류: {str(e)}") from e
    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        logger.error("실시간 이메일 발송 네트워크 오류", exception=e, to_email=to_email)
        raise HTTPException(status_code=503, detail=f"이메일 발송 네트워크 오류: {str(e)}") from e
    except Exception as e:
        logger.error("실시간 이메일 발송 예상치 못한 오류", exception=e, to_email=to_email)
        raise EmailNotificationError(
            f"이메일 발송 실패: {str(e)}",
            error_code="EMAIL_SEND_FAILED",
            cause=e
        ) from e

@app.post("/api/airflow/trigger-dag",
         summary="Airflow DAG 트리거",
         description="지정된 Airflow DAG를 즉시 실행합니다. 실시간 이벤트 발생 시 DAG를 트리거할 때 사용합니다.",
         responses={
             200: {"description": "DAG가 성공적으로 트리거되었습니다."},
             400: {"description": "잘못된 요청입니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def trigger_airflow_dag(
    dag_id: str = Query(..., description="트리거할 DAG ID (예: email_notification_dag)"),
    airflow_host: Optional[str] = Query(None, description="Airflow 호스트 (기본값: localhost)"),
    airflow_port: Optional[int] = Query(None, description="Airflow 포트 (기본값: 8081)"),
    conf: Optional[Dict[str, Any]] = Body(None, description="DAG 실행 시 전달할 설정 (JSON)")
):
    try:
        import requests
        
        airflow_host = airflow_host or os.getenv('AIRFLOW_HOST', 'localhost')
        airflow_port = airflow_port or int(os.getenv('AIRFLOW_PORT', '8081'))
        
        airflow_url = f"http://{airflow_host}:{airflow_port}"
        trigger_url = f"{airflow_url}/api/v1/dags/{dag_id}/dagRuns"
        
        airflow_username = os.getenv('AIRFLOW_USERNAME', 'airflow')
        airflow_password = os.getenv('AIRFLOW_PASSWORD', 'airflow')
        
        logger.info("Airflow DAG 트리거 시도", dag_id=dag_id, airflow_url=airflow_url)
        
        payload = {
            "dag_run_id": f"manual__{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "conf": conf or {}
        }
        
        response = requests.post(
            trigger_url,
            json=payload,
            auth=(airflow_username, airflow_password),
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Airflow DAG 트리거 성공", dag_id=dag_id, dag_run_id=result.get('dag_run_id'))
            return {
                "success": True,
                "message": f"DAG '{dag_id}'가 성공적으로 트리거되었습니다.",
                "dag_run_id": result.get('dag_run_id'),
                "state": result.get('state')
            }
        elif response.status_code == 401:
            logger.error("Airflow 인증 실패", dag_id=dag_id)
            raise HTTPException(
                status_code=401,
                detail="Airflow 인증에 실패했습니다. AIRFLOW_USERNAME과 AIRFLOW_PASSWORD를 확인하세요."
            )
        elif response.status_code == 404:
            logger.error("Airflow DAG를 찾을 수 없음", dag_id=dag_id)
            raise HTTPException(
                status_code=404,
                detail=f"DAG '{dag_id}'를 찾을 수 없습니다."
            )
        else:
            error_msg = response.text
            logger.error("Airflow DAG 트리거 실패", dag_id=dag_id, status_code=response.status_code, error=error_msg)
            raise HTTPException(
                status_code=500,
                detail=f"Airflow DAG 트리거 실패: {error_msg}"
            )
    except requests.exceptions.ConnectionError as e:
        logger.error("Airflow 연결 실패", exception=e, dag_id=dag_id)
        raise HTTPException(
            status_code=503,
            detail=f"Airflow 서버에 연결할 수 없습니다. Airflow가 실행 중인지 확인하세요."
        ) from e
    except requests.exceptions.Timeout as e:
        logger.error("Airflow 요청 타임아웃", exception=e, dag_id=dag_id)
        raise HTTPException(
            status_code=504,
            detail="Airflow 서버 응답 시간이 초과되었습니다."
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Airflow DAG 트리거 예상치 못한 오류", exception=e, dag_id=dag_id)
        raise HTTPException(
            status_code=500,
            detail=f"Airflow DAG 트리거 중 오류 발생: {str(e)}"
        ) from e

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_ip: str = "unknown") -> None:
    await manager.connect(websocket, client_ip)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_personal_message("pong", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket, client_ip: str = "unknown") -> None:
    await manager.connect(websocket, client_ip)
    try:
        if not hasattr(websocket.app.state, 'data_collector'):
            await manager.send_personal_message(json.dumps({"error": "서비스 초기화 중입니다"}), websocket)
            return
        
        api = StockAnalysisAPI(
            data_collector=websocket.app.state.data_collector,
            analyzer=websocket.app.state.analyzer,
            security_manager=websocket.app.state.security_manager,
            error_manager=websocket.app.state.error_manager,
            news_collector=NewsCollector()
        )
        while True:
            try:
                analysis_data = await api.get_all_symbols_analysis()
                await manager.send_personal_message(json.dumps(analysis_data, default=str), websocket)
                await asyncio.sleep(5)
            except (StockAnalysisError, StockDataCollectionError) as e:
                logger.error(f"WebSocket 스트리밍 분석 오류: {str(e)}")
                await asyncio.sleep(1)
            except WebSocketError as e:
                logger.error(f"WebSocket 스트리밍 연결 오류: {str(e)}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"WebSocket 스트리밍 예상치 못한 오류: {str(e)}")
                await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except WebSocketConnectionError as e:
        logger.error(f"WebSocket 연결 오류: {str(e)}")
        manager.disconnect(websocket)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_id = f"ERR_{int(time.time())}_{hash(str(exc)) % 10000}"
    
    if isinstance(exc, StockAnalysisBaseException):
        logger.error(
            f"커스텀 예외 발생: {type(exc).__name__}, "
            f"메시지: {str(exc)}, 오류 ID: {error_id}, "
            f"경로: {str(request.url)}, "
            f"원인: {type(exc.cause).__name__ if exc.cause else 'None'}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "error_type": type(exc).__name__,
                "error_code": exc.error_code,
                "error_id": error_id,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url)
            }
        )
    
    logger.error(f"처리되지 않은 예외: {str(exc)}, 오류 ID: {error_id}, 경로: {str(request.url)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "서버 내부 오류",
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

async def _fetch_news_with_fallback(api: StockAnalysisAPI, symbol: str, include_korean: bool, 
                                     auto_translate: bool, timeout: float) -> List[Dict[str, Any]]:
    try:
        news = await asyncio.wait_for(
            asyncio.to_thread(
                api.news_collector.get_stock_news,
                symbol.upper(),
                include_korean=include_korean,
                auto_translate=auto_translate
            ),
            timeout=timeout
        )
        return news if news else []
    except (asyncio.TimeoutError, TimeoutError):
        if auto_translate:
            logger.warning(f"번역 타임아웃: {symbol}, 번역 없이 재시도")
            try:
                news = await asyncio.wait_for(
                    asyncio.to_thread(
                        api.news_collector.get_stock_news,
                        symbol.upper(),
                        include_korean=include_korean,
                        auto_translate=False
                    ),
                    timeout=15.0
                )
                return news if news else []
            except Exception as e:
                logger.warning(f"번역 없이 뉴스 수집 실패: {symbol} - {str(e)}")
        return []
    except (ConnectionError, NetworkError) as e:
        logger.warning(f"뉴스 조회 네트워크 오류: {symbol} - {str(e)}")
        return []
    except Exception as e:
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            if auto_translate:
                try:
                    news = await asyncio.wait_for(
                        asyncio.to_thread(
                            api.news_collector.get_stock_news,
                            symbol.upper(),
                            include_korean=include_korean,
                            auto_translate=False
                        ),
                        timeout=15.0
                    )
                    return news if news else []
                except Exception:
                    pass
        logger.warning(f"뉴스 조회 오류: {symbol} - {str(e)}")
        return []

@app.get("/api/news/{symbol}",
         summary="종목별 뉴스 조회",
         description="특정 종목에 관련된 뉴스를 조회합니다.",
         response_model=List[NewsResponse],
         responses={
             200: {"description": "성공적으로 뉴스를 조회했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse},
             503: {"description": "서비스가 일시적으로 사용 불가능합니다.", "model": ErrorResponse}
         })
async def get_stock_news(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    include_korean: bool = Query(False, description="한국어 뉴스 포함 여부"),
    auto_translate: bool = Query(False, description="한국어 뉴스 번역 여부"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> List[NewsResponse]:
    logger.info(f"뉴스 조회 요청: {symbol}, include_korean={include_korean}, auto_translate={auto_translate}")
    
    timeout_seconds = 25.0 if auto_translate else 20.0
    news = await _fetch_news_with_fallback(api, symbol, include_korean, auto_translate, timeout_seconds)
    
    if not news:
        logger.info(f"뉴스 조회 결과 없음: {symbol}")
        return []
    
    logger.info(f"뉴스 수집 완료: {symbol} - {len(news)}개")
    try:
        return [NewsResponse(**item) for item in news]
    except Exception as e:
        logger.error(f"뉴스 응답 변환 오류: {symbol} - {str(e)}", exc_info=True)
        return []

@app.get("/api/news",
         summary="뉴스 검색",
         description="키워드로 뉴스를 검색합니다.",
         response_model=List[NewsResponse],
         responses={
             200: {"description": "성공적으로 뉴스를 검색했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def search_news(
    query: str = Query(..., description="검색 키워드", example="Apple"),
    language: str = Query("en", description="언어 (en/ko)", example="en"),
    max_results: int = Query(20, description="최대 결과 수", ge=1, le=100),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> List[NewsResponse]:
    try:
        news = api.news_collector.search_news(query, language=language, max_results=max_results)
        return [NewsResponse(**item) for item in news]
    except (TimeoutError, ConnectionError, NetworkError) as e:
        logger.error(f"뉴스 검색 네트워크 오류: {str(e)}")
        raise HTTPException(status_code=503, detail=f"뉴스 검색 네트워크 오류: {str(e)}") from e
    except Exception as e:
        logger.error(f"뉴스 검색 예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 검색 오류: {str(e)}") from e

@app.get("/api/news/multiple",
         summary="다중 종목 뉴스 조회",
         description="여러 종목의 뉴스를 한번에 조회합니다.",
         responses={
             200: {"description": "성공적으로 뉴스를 조회했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_multiple_stock_news(
    symbols: str = Query(..., description="종목 심볼들 (쉼표로 구분)", example="AAPL,GOOGL,MSFT"),
    include_korean: bool = Query(False, description="한국어 뉴스 포함 여부"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> Dict[str, List[NewsResponse]]:
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        if len(symbol_list) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 symbols allowed per request"
            )
        news_dict = api.news_collector.get_multiple_stock_news(symbol_list, include_korean=include_korean)
        return {
            symbol: [NewsResponse(**item) for item in news_list]
            for symbol, news_list in news_dict.items()
        }
    except HTTPException:
        raise
    except (TimeoutError, ConnectionError, NetworkError) as e:
        logger.error(f"다중 종목 뉴스 조회 네트워크 오류: {str(e)}")
        raise HTTPException(status_code=503, detail=f"다중 종목 뉴스 조회 네트워크 오류: {str(e)}") from e
    except Exception as e:
        logger.error(f"다중 종목 뉴스 조회 예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"다중 종목 뉴스 조회 오류: {str(e)}") from e

@app.get("/api/sectors",
         summary="섹터별 분석",
         description="섹터별로 그룹화된 종목 분석 결과를 조회합니다.",
         responses={
             200: {"description": "성공적으로 섹터별 분석 결과를 조회했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_sectors_analysis(
    api: StockAnalysisAPI = Depends(get_stock_api),
    basic_analyzer: TechnicalAnalyzer = Depends(get_basic_analyzer),
    enhanced_collector: StockDataCollector = Depends(get_enhanced_collector)
):
    try:
        from collections import defaultdict
        import random
        
        sector_mapping = {
            "AAPL": "Technology",
            "GOOGL": "Technology",
            "MSFT": "Technology",
            "NVDA": "Technology",
            "META": "Technology",
            "AMZN": "Consumer Discretionary",
            "TSLA": "Consumer Discretionary",
            "NFLX": "Communication Services"
        }
        
        results = await api.get_all_symbols_analysis(basic_analyzer, enhanced_collector)
        sectors = defaultdict(list)
        
        for result in results:
            symbol = result.get('symbol', '')
            sector = sector_mapping.get(symbol, 'Other')
            change_percent = result.get('changePercent', 0.0)
            current_price = result.get('currentPrice', 0.0)
            volume = result.get('volume', 0)
            signals = result.get('signals', {})
            confidence = signals.get('confidence', 0.0) if isinstance(signals, dict) else 0.0
            
            sectors[sector].append({
                'symbol': symbol,
                'currentPrice': current_price,
                'changePercent': change_percent,
                'volume': volume,
                'confidence': confidence,
                'signal': signals.get('signal', 'hold') if isinstance(signals, dict) else 'hold'
            })
        
        sector_data = []
        for sector_name, stocks in sectors.items():
            if not stocks:
                continue
                
            avg_change = sum(s['changePercent'] for s in stocks) / len(stocks)
            total_volume = sum(s['volume'] for s in stocks)
            avg_confidence = sum(s['confidence'] for s in stocks) / len(stocks)
            
            sector_data.append({
                'sector': sector_name,
                'stocks': stocks,
                'avgChangePercent': avg_change,
                'totalVolume': total_volume,
                'avgConfidence': avg_confidence,
                'stockCount': len(stocks)
            })
        
        if not sector_data:
            logger.warning("섹터 데이터가 없어 더미 데이터를 반환합니다.")
            sector_data = [
                {
                    'sector': 'Technology',
                    'stocks': [
                        {'symbol': 'AAPL', 'currentPrice': 175.50, 'changePercent': 2.30, 'volume': 50000000, 'confidence': 0.75, 'signal': 'buy'},
                        {'symbol': 'GOOGL', 'currentPrice': 142.80, 'changePercent': 1.80, 'volume': 30000000, 'confidence': 0.70, 'signal': 'hold'},
                        {'symbol': 'MSFT', 'currentPrice': 378.90, 'changePercent': 2.50, 'volume': 25000000, 'confidence': 0.80, 'signal': 'buy'},
                        {'symbol': 'NVDA', 'currentPrice': 485.20, 'changePercent': 3.20, 'volume': 40000000, 'confidence': 0.85, 'signal': 'buy'}
                    ],
                    'avgChangePercent': 2.45,
                    'totalVolume': 145000000,
                    'avgConfidence': 0.775,
                    'stockCount': 4
                },
                {
                    'sector': 'Consumer Discretionary',
                    'stocks': [
                        {'symbol': 'AMZN', 'currentPrice': 145.30, 'changePercent': 2.10, 'volume': 35000000, 'confidence': 0.65, 'signal': 'hold'},
                        {'symbol': 'TSLA', 'currentPrice': 245.20, 'changePercent': 1.80, 'volume': 60000000, 'confidence': 0.70, 'signal': 'hold'}
                    ],
                    'avgChangePercent': 1.95,
                    'totalVolume': 95000000,
                    'avgConfidence': 0.675,
                    'stockCount': 2
                },
                {
                    'sector': 'Communication Services',
                    'stocks': [
                        {'symbol': 'META', 'currentPrice': 312.40, 'changePercent': 1.90, 'volume': 28000000, 'confidence': 0.72, 'signal': 'hold'},
                        {'symbol': 'NFLX', 'currentPrice': 425.60, 'changePercent': 1.50, 'volume': 15000000, 'confidence': 0.68, 'signal': 'hold'}
                    ],
                    'avgChangePercent': 1.70,
                    'totalVolume': 43000000,
                    'avgConfidence': 0.70,
                    'stockCount': 2
                }
            ]
        
        sector_data.sort(key=lambda x: x['avgChangePercent'], reverse=True)
        return sector_data
    except Exception as e:
        logger.error(f"섹터별 분석 오류: {str(e)}", exc_info=True)
        logger.warning("섹터 분석 오류로 인해 더미 데이터를 반환합니다.")
        return [
            {
                'sector': 'Technology',
                'stocks': [
                    {'symbol': 'AAPL', 'currentPrice': 175.50, 'changePercent': 2.30, 'volume': 50000000, 'confidence': 0.75, 'signal': 'buy'},
                    {'symbol': 'GOOGL', 'currentPrice': 142.80, 'changePercent': 1.80, 'volume': 30000000, 'confidence': 0.70, 'signal': 'hold'},
                    {'symbol': 'MSFT', 'currentPrice': 378.90, 'changePercent': 2.50, 'volume': 25000000, 'confidence': 0.80, 'signal': 'buy'}
                ],
                'avgChangePercent': 2.20,
                'totalVolume': 105000000,
                'avgConfidence': 0.75,
                'stockCount': 3
            },
            {
                'sector': 'Consumer Discretionary',
                'stocks': [
                    {'symbol': 'AMZN', 'currentPrice': 145.30, 'changePercent': 2.10, 'volume': 35000000, 'confidence': 0.65, 'signal': 'hold'},
                    {'symbol': 'TSLA', 'currentPrice': 245.20, 'changePercent': 1.80, 'volume': 60000000, 'confidence': 0.70, 'signal': 'hold'}
                ],
                'avgChangePercent': 1.95,
                'totalVolume': 95000000,
                'avgConfidence': 0.675,
                'stockCount': 2
            }
        ]

@app.get("/api/news/detail",
         summary="뉴스 상세보기",
         description="뉴스 URL로 상세 정보를 조회합니다.")
async def get_news_detail(
    url: str = Query(..., description="뉴스 URL"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> NewsResponse:
    try:
        import urllib.parse
        decoded_url = url
        for _ in range(3):
            try:
                decoded_url = urllib.parse.unquote(decoded_url, encoding='utf-8')
            except Exception:
                break
        
        decoded_url = decoded_url.replace('&amp;', '&')
        
        logger.info(f"뉴스 상세 조회 요청: url={url[:100]}..., decoded_url={decoded_url[:100]}...")
        
        news = await asyncio.wait_for(
            asyncio.to_thread(
                api.news_collector.get_news_by_url,
                decoded_url
            ),
            timeout=25.0
        )
        if not news:
            logger.warning(f"뉴스를 찾을 수 없습니다: {decoded_url[:100]}...")
            raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")
        
        return NewsResponse(**news)
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        logger.warning(f"뉴스 상세 조회 타임아웃: url={url[:100]}...")
        raise HTTPException(status_code=503, detail="뉴스 상세 조회 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
    except TimeoutError as e:
        logger.warning(f"뉴스 상세 조회 타임아웃: url={url[:100]}...")
        raise HTTPException(status_code=503, detail="뉴스 상세 조회 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.") from e
    except (ConnectionError, NetworkError) as e:
        logger.error(f"뉴스 상세 조회 네트워크 오류: url={url[:100]}..., error={str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"뉴스 상세 조회 네트워크 오류: {str(e)}") from e
    except Exception as e:
        logger.error(f"뉴스 상세 조회 예상치 못한 오류: url={url[:100]}..., error={str(e)}", exc_info=True)
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            raise HTTPException(status_code=503, detail="뉴스 상세 조회 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.") from e
        raise HTTPException(status_code=500, detail=f"뉴스 상세 조회 오류: {str(e)}") from e


if __name__ == "__main__":
    import platform
    reload_enabled = platform.system() != 'Windows'
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=9000,
        reload=reload_enabled
    )
