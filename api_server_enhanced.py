from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path, Request, Depends, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from typing import Protocol, TypedDict, List, Dict, Optional, Union, Any
import asyncio
import json
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

from data_collectors.performance_optimized_collector import PerformanceOptimizedCollector
from data_collectors.stock_data_collector import StockDataCollector
from data_collectors.news_collector import NewsCollector
from analysis_engine.advanced_analyzer import AdvancedTechnicalAnalyzer
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService
from security.security_manager import SecurityManager, SecurityConfig
from error_handling.error_manager import ErrorManager, ErrorSeverity, ErrorCategory, error_handler, ErrorContext
from config.settings import get_settings
from config.logging_config import get_logger
import re

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False
    logger = get_logger(__name__, "stock_analysis.log")
    logger.debug("pymysql 모듈이 설치되지 않았습니다. 이메일 발송 이력 저장 기능이 비활성화됩니다.")

settings = get_settings()
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
    logger.info("애플리케이션 시작: 서비스 초기화 중")
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
        
    except Exception as e:
        logger.error(f"애플리케이션 시작 오류: {str(e)}", exc_info=True)
        raise
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
                
                return {
                    'symbol': data['symbol'],
                    'currentPrice': data['price'],
                    'volume': data.get('volume', 0),
                    'changePercent': data.get('change_percent', 0),
                    'timestamp': data.get('timestamp', datetime.now()),
                    'confidenceScore': confidence_score
                }
                
            except HTTPException:
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                
                error_id = self.error_manager.log_error(
                    ErrorSeverity.HIGH,
                    ErrorCategory.DATA_COLLECTION,
                    f"실시간 데이터 조회 오류: {symbol} ({max_retries}회 시도 후) - {str(e)}",
                    e,
                    context
                )
                logger.error(f"실시간 데이터 조회 오류: {symbol}, 오류 ID: {error_id}, 시도 횟수: {attempt+1}, 오류: {str(e)}")
                
                fallback_data = await self._get_fallback_data(symbol)
                if fallback_data:
                    logger.warning(f"{symbol}에 대한 대체 데이터 사용 중")
                    return fallback_data
                
                raise HTTPException(
                    status_code=500,
                    detail=f"서버 내부 오류. 오류 ID: {error_id}"
                )
    
    async def _get_fallback_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            from data_collectors.stock_data_collector import StockDataCollector
            fallback_collector = StockDataCollector([symbol], use_mock_data=True, fallback_to_mock=True)
            fallback_data = fallback_collector.get_realtime_data(symbol)
            
            if fallback_data and fallback_data.get('price', 0) > 0:
                return {
                    'symbol': fallback_data['symbol'],
                    'currentPrice': fallback_data['price'],
                    'volume': fallback_data.get('volume', 0),
                    'changePercent': fallback_data.get('change_percent', 0),
                    'timestamp': fallback_data.get('timestamp', datetime.now()),
                    'confidenceScore': 0.3
                }
        except Exception as e:
            logger.error(f"{symbol}에 대한 대체 데이터 조회 실패: {str(e)}")
        
        return None
    
    async def get_advanced_analysis(self, symbol: str) -> Dict[str, Any]:
        context = ErrorContext(
            endpoint=f"/api/analysis/{symbol}",
            parameters={'symbol': symbol}
        )
        
        try:
            realtime_data = await self.get_realtime_data_enhanced(symbol)
            
            historical_data = None
            max_retries = 2
            
            for attempt in range(max_retries):
                try:
                    historical_data = await self.data_collector.get_historical_data_async(symbol, "3mo")
                    if not historical_data.empty:
                        break
                except Exception as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2.0 * (attempt + 1))
                        continue
                    else:
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
                            )
            
            try:
                analyzed_data = self.analyzer.calculate_all_advanced_indicators(historical_data)
            except Exception as e:
                error_id = self.error_manager.log_error(
                    ErrorSeverity.MEDIUM,
                    ErrorCategory.ANALYSIS,
                    f"지표 계산 오류: {symbol} - {str(e)}",
                    e,
                    context
                )
                analyzed_data = historical_data
            
            try:
                market_regime = self.analyzer.calculate_market_regime(analyzed_data)
            except Exception as e:
                logger.warning(f"{symbol}에 대한 시장 상황 계산 오류: {str(e)}")
                market_regime = {'regime': 'unknown', 'confidence': 0.0}
            
            try:
                patterns = self.analyzer.detect_chart_patterns(analyzed_data)
            except Exception as e:
                logger.warning(f"{symbol}에 대한 패턴 감지 오류: {str(e)}")
                patterns = []
            
            try:
                support_resistance = self.analyzer.calculate_support_resistance(analyzed_data)
            except Exception as e:
                logger.warning(f"{symbol}에 대한 지지/저항선 계산 오류: {str(e)}")
                support_resistance = {'support': [], 'resistance': []}
            
            try:
                fibonacci_levels = self.analyzer.calculate_fibonacci_levels(analyzed_data)
            except Exception as e:
                logger.warning(f"{symbol}에 대한 피보나치 레벨 계산 오류: {str(e)}")
                fibonacci_levels = {}
            
            try:
                anomalies = self.analyzer.detect_anomalies_ml(analyzed_data)
            except Exception as e:
                logger.warning(f"{symbol}에 대한 이상 패턴 감지 오류: {str(e)}")
                anomalies = []
            
            try:
                signals = self.analyzer.calculate_advanced_signals(analyzed_data)
            except Exception as e:
                logger.warning(f"{symbol}에 대한 신호 계산 오류: {str(e)}")
                signals = {'signal': 'hold', 'confidence': 0.0, 'signals': []}
            
            risk_score = self._calculate_risk_score(analyzed_data, anomalies)
            confidence = self._calculate_analysis_confidence(analyzed_data, market_regime)
            
            return {
                'symbol': symbol,
                'currentPrice': realtime_data['currentPrice'],
                'volume': realtime_data.get('volume', 0),
                'changePercent': realtime_data.get('changePercent', 0),
                'trend': signals.get('signal', 'hold'),
                'trendStrength': signals.get('confidence', 0.0),
                'marketRegime': market_regime.get('regime', 'unknown'),
                'signals': signals,
                'patterns': patterns,
                'supportResistance': support_resistance,
                'fibonacciLevels': fibonacci_levels,
                'anomalies': [
                    {
                        'type': anomaly.get('type', 'unknown'),
                        'severity': anomaly.get('severity', 'low'),
                        'message': anomaly.get('message', f"이상 패턴 감지: {anomaly.get('type', 'unknown')}"),
                        'timestamp': datetime.now().isoformat()
                    } for anomaly in anomalies
                ],
                'riskScore': risk_score,
                'confidence': confidence,
                'timestamp': datetime.now()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            error_id = self.error_manager.log_error(
                ErrorSeverity.HIGH,
                ErrorCategory.ANALYSIS,
                f"고급 분석 오류: {symbol} - {str(e)}",
                e,
                context
            )
            logger.error(f"고급 분석 오류: {symbol}, 오류 ID: {error_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"분석 오류. 오류 ID: {error_id}"
            )
    
    async def _get_fallback_historical_data(self, symbol: str) -> pd.DataFrame:
        try:
            from data_collectors.stock_data_collector import StockDataCollector
            fallback_collector = StockDataCollector([symbol], use_mock_data=True, fallback_to_mock=True)
            return fallback_collector.get_historical_data(symbol, "3mo")
        except Exception as e:
            logger.error(f"{symbol}에 대한 대체 과거 데이터 조회 실패: {str(e)}")
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
                    logger.error(f"종목 분석 오류: {symbols[i]}, 오류: {str(result)}")
                    continue
                if result:
                    valid_results.append(result)
            
            return valid_results
            
        except Exception as e:
            error_id = self.error_manager.log_error(
                ErrorSeverity.MEDIUM,
                ErrorCategory.ANALYSIS,
                f"배치 분석 오류: {str(e)}",
                e
            )
            logger.error(f"배치 분석 오류: {str(e)}, 오류 ID: {error_id}")
            raise HTTPException(
                status_code=500,
                detail=f"배치 분석 오류. 오류 ID: {error_id}"
            )
    
    def _load_historical_data(self, symbol: str, request: Request):
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
    
    async def get_basic_analysis(self, symbol: str, request: Request) -> Dict[str, Any]:
        try:
            from analysis_engine.technical_analyzer import TechnicalAnalyzer
            basic_analyzer = request.app.state.basic_analyzer
            enhanced_collector = request.app.state.enhanced_collector
            
            realtime_data = enhanced_collector.get_realtime_data(symbol)
            if not realtime_data:
                raise HTTPException(status_code=404, detail=f"종목 데이터를 찾을 수 없습니다: {symbol}")
            
            historical_data = self._load_historical_data(symbol, request)
            
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
        except Exception as e:
            logger.error(f"분석 오류 ({symbol}): {str(e)}")
            raise HTTPException(status_code=500, detail=f"분석 오류: {str(e)}")
    
    async def get_all_symbols_analysis(self, request: Optional[Request] = None) -> List[Dict[str, Any]]:
        try:
            results = []
            for symbol in settings.ANALYSIS_SYMBOLS:
                try:
                    if request:
                        analysis = await self.get_basic_analysis(symbol, request)
                    else:
                        analysis = await self.get_advanced_analysis(symbol)
                    results.append(analysis)
                except Exception as e:
                    logger.error(f"{symbol} 분석 오류: {str(e)}")
                    continue
            return results
        except Exception as e:
            logger.error(f"전체 종목 분석 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"전체 종목 분석 오류: {str(e)}")
    
    async def get_historical_data(self, symbol: str, days: int, request: Request) -> Dict[str, Any]:
        try:
            from analysis_engine.technical_analyzer import TechnicalAnalyzer
            basic_analyzer = request.app.state.basic_analyzer
            
            historical_data = self._load_historical_data(symbol, request)
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
        except Exception as e:
            logger.error(f"과거 데이터 조회 오류 ({symbol}): {str(e)}")
            raise HTTPException(status_code=500, detail=f"과거 데이터 조회 오류: {str(e)}")

def get_stock_api(request: Request) -> StockAnalysisAPI:
    return StockAnalysisAPI(
        data_collector=request.app.state.data_collector,
        analyzer=request.app.state.analyzer,
        security_manager=request.app.state.security_manager,
        error_manager=request.app.state.error_manager,
        news_collector=NewsCollector()
    )

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
         description="API 서버의 상태를 확인합니다.",
         response_model=Dict[str, Union[str, float]])
async def health_check(api: StockAnalysisAPI = Depends(get_stock_api)) -> Dict[str, Any]:
    try:
        health_data = await api.data_collector.health_check()
        performance_metrics = api.data_collector.get_performance_metrics()
        
        return {
            "status": health_data['status'],
            "timestamp": datetime.now().isoformat(),
            "performance": performance_metrics,
            "connections": manager.get_connection_stats(),
            "errors": api.error_manager.get_error_statistics(hours=1)
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        return {
            "status": "unhealthy",
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
    request: Request,
    api: StockAnalysisAPI = Depends(get_stock_api)
):
    return await api.get_all_symbols_analysis(request)

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
    request: Request,
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    api: StockAnalysisAPI = Depends(get_stock_api)
):
    result = await api.get_basic_analysis(symbol, request)
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
    request: Request,
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    days: int = Query(30, description="조회할 일수", ge=1, le=365),
    api: StockAnalysisAPI = Depends(get_stock_api)
):
    return await api.get_historical_data(symbol, days, request)

@app.get("/api/alpha-vantage/search/{keywords}",
         summary="Alpha Vantage 종목 검색",
         description="Alpha Vantage API를 사용하여 종목을 검색합니다.",
         responses={
             200: {"description": "성공적으로 종목을 검색했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def search_symbols(
    request: Request,
    keywords: str = Path(..., description="검색 키워드", example="Apple")
):
    try:
        enhanced_collector = request.app.state.enhanced_collector
        return enhanced_collector.search_alpha_vantage_symbols(keywords)
    except Exception as e:
        logger.error(f"종목 검색 오류 ({keywords}): {str(e)}")
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
    request: Request,
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    interval: str = Query("5min", description="시간 간격", example="5min"),
    outputsize: str = Query("compact", description="출력 크기", example="compact")
):
    try:
        enhanced_collector = request.app.state.enhanced_collector
        data = enhanced_collector.get_alpha_vantage_intraday_data(symbol, interval, outputsize)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"분별 데이터를 찾을 수 없습니다: {symbol}")
        return data.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분별 데이터 조회 오류 ({symbol}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"분별 데이터 조회 오류: {str(e)}")

@app.get("/api/alpha-vantage/weekly/{symbol}",
         summary="Alpha Vantage 주별 데이터",
         description="Alpha Vantage API를 사용하여 주별 주가 데이터를 조회합니다.",
         responses={
             200: {"description": "성공적으로 주별 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_alpha_vantage_weekly(
    request: Request,
    symbol: str = Path(..., description="주식 심볼", example="AAPL")
):
    try:
        enhanced_collector = request.app.state.enhanced_collector
        data = enhanced_collector.get_alpha_vantage_weekly_data(symbol)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"주별 데이터를 찾을 수 없습니다: {symbol}")
        return data.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"주별 데이터 조회 오류 ({symbol}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"주별 데이터 조회 오류: {str(e)}")

@app.get("/api/alpha-vantage/monthly/{symbol}",
         summary="Alpha Vantage 월별 데이터",
         description="Alpha Vantage API를 사용하여 월별 주가 데이터를 조회합니다.",
         responses={
             200: {"description": "성공적으로 월별 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_alpha_vantage_monthly(
    request: Request,
    symbol: str = Path(..., description="주식 심볼", example="AAPL")
):
    try:
        enhanced_collector = request.app.state.enhanced_collector
        data = enhanced_collector.get_alpha_vantage_monthly_data(symbol)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"월별 데이터를 찾을 수 없습니다: {symbol}")
        return data.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"월별 데이터 조회 오류 ({symbol}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"월별 데이터 조회 오류: {str(e)}")

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
    request: Request,
    to_email: Optional[str] = Query(None, description="수신자 이메일"),
    subject: Optional[str] = Query(None, description="이메일 제목"),
    body: Optional[str] = Query(None, description="이메일 내용"),
    request_body: Optional[EmailNotificationRequest] = Body(None, description="요청 본문")
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
        
        notification_service = request.app.state.notification_service
        success = notification_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )
        
        if PYMYSQL_AVAILABLE:
            try:
                conn = pymysql.connect(
                    host=settings.MYSQL_HOST,
                    user=settings.MYSQL_USER,
                    password=settings.MYSQL_PASSWORD,
                    database=settings.MYSQL_DATABASE,
                    port=settings.MYSQL_PORT,
                    charset='utf8mb4'
                )
                cursor = conn.cursor()
                
                log_message = f"[API발송] {subject}\n{body}"
                status = "sent" if success else "failed"
                error_msg = None if success else "이메일 발송에 실패했습니다."
                
                cursor.execute("""
                    INSERT INTO notification_logs 
                    (user_email, symbol, notification_type, message, status, sent_at, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    to_email,
                    None,
                    'email',
                    log_message,
                    status,
                    datetime.now(),
                    error_msg
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                logger.info(f"이메일 발송 이력 저장 완료: {to_email} - {status}")
            except Exception as e:
                logger.error(f"이메일 발송 이력 저장 실패: {str(e)}")
        
        if success:
            return EmailNotificationResponse(
                success=True,
                message="이메일이 성공적으로 발송되었습니다."
            )
        else:
            return EmailNotificationResponse(
                success=False,
                message="이메일 발송에 실패했습니다."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이메일 발송 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이메일 발송 오류: {str(e)}")

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
    request: Request,
    from_phone: Optional[str] = Query(None, description="발신번호 (01012345678 형식)"),
    to_phone: Optional[str] = Query(None, description="수신번호 (01012345678 형식)"),
    message: Optional[str] = Query(None, description="메시지 내용"),
    request_body: Optional[SmsNotificationRequest] = Body(None, description="요청 본문")
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
        
        notification_service = request.app.state.notification_service
        success = notification_service.send_sms(
            from_phone=from_phone,
            to_phone=to_phone,
            message=message
        )
        
        if PYMYSQL_AVAILABLE:
            try:
                conn = pymysql.connect(
                    host=settings.MYSQL_HOST,
                    user=settings.MYSQL_USER,
                    password=settings.MYSQL_PASSWORD,
                    database=settings.MYSQL_DATABASE,
                    port=settings.MYSQL_PORT,
                    charset='utf8mb4'
                )
                cursor = conn.cursor()
                
                log_message = f"[API발송] {message}"
                status = "sent" if success else "failed"
                error_msg = None if success else "문자 발송에 실패했습니다."
                
                cursor.execute("""
                    INSERT INTO notification_logs 
                    (user_email, symbol, notification_type, message, status, sent_at, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    to_phone,
                    None,
                    'sms',
                    log_message,
                    status,
                    datetime.now(),
                    error_msg
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                logger.info(f"문자 발송 이력 저장 완료: {to_phone} - {status}")
            except Exception as e:
                logger.error(f"문자 발송 이력 저장 실패: {str(e)}")
        
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
    except Exception as e:
        logger.error(f"문자 발송 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문자 발송 오류: {str(e)}")

@app.get("/api/notifications/sms-config",
         summary="SMS 발신번호 조회",
         description="설정된 SMS 발신번호를 조회합니다.")
async def get_sms_config():
    try:
        from_phone = settings.SOLAPI_FROM_PHONE
        return {
            "fromPhone": from_phone
        }
    except Exception as e:
        logger.error(f"SMS 설정 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SMS 설정 조회 오류: {str(e)}")

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
            except Exception as e:
                logger.error(f"WebSocket 스트리밍 오류: {str(e)}")
                await asyncio.sleep(1)
    except WebSocketDisconnect:
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
    logger.info(f"뉴스 조회 요청 받음: {symbol}, include_korean={include_korean}, auto_translate={auto_translate}")
    try:
        timeout_seconds = 25.0 if auto_translate else 20.0
        logger.info(f"뉴스 수집 시작: {symbol} (타임아웃: {timeout_seconds}초)")
        
        try:
            news = await asyncio.wait_for(
                asyncio.to_thread(
                    api.news_collector.get_stock_news,
                    symbol.upper(),
                    include_korean=include_korean,
                    auto_translate=auto_translate
                ),
                timeout=timeout_seconds
            )
            logger.info(f"뉴스 수집 완료: {symbol} - {len(news) if news else 0}개")
            if not news:
                logger.info(f"뉴스 조회 결과 없음: {symbol}")
                return []
            return [NewsResponse(**item) for item in news]
        except asyncio.TimeoutError:
            if auto_translate:
                logger.warning(f"번역 타임아웃: {symbol}, 번역 없이 뉴스 수집 시도")
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
                    if news:
                        logger.info(f"번역 없이 뉴스 수집 완료: {symbol} - {len(news)}개")
                        return [NewsResponse(**item) for item in news]
                except Exception as e:
                    logger.warning(f"번역 없이 뉴스 수집 실패: {str(e)}")
            logger.warning(f"뉴스 조회 타임아웃: {symbol}, 빈 리스트 반환")
            return []
    except Exception as e:
        logger.error(f"뉴스 조회 오류: {symbol} - {str(e)}", exc_info=True)
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
                    if news:
                        logger.info(f"번역 없이 뉴스 수집 완료: {symbol} - {len(news)}개")
                        return [NewsResponse(**item) for item in news]
                except Exception as e2:
                    logger.warning(f"번역 없이 뉴스 수집 실패: {str(e2)}")
            logger.warning(f"뉴스 조회 타임아웃: {symbol}, 빈 리스트 반환")
            return []
        logger.warning(f"뉴스 조회 실패, 빈 리스트 반환: {symbol} - {str(e)}")
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
    except Exception as e:
        logger.error(f"뉴스 검색 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 검색 오류: {str(e)}")

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
    except Exception as e:
        logger.error(f"다중 종목 뉴스 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"다중 종목 뉴스 조회 오류: {str(e)}")

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
    except Exception as e:
        logger.error(f"뉴스 상세 조회 오류: url={url[:100]}..., error={str(e)}", exc_info=True)
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            raise HTTPException(status_code=503, detail="뉴스 상세 조회 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
        raise HTTPException(status_code=500, detail=f"뉴스 상세 조회 오류: {str(e)}")


if __name__ == "__main__":
    import platform
    reload_enabled = platform.system() != 'Windows'
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=9000,
        reload=reload_enabled
    )
