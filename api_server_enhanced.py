from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path, Request, Depends, status
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
    create_cors_middleware_config
)

from data_collectors.performance_optimized_collector import PerformanceOptimizedCollector
from data_collectors.news_collector import NewsCollector
from analysis_engine.advanced_analyzer import AdvancedTechnicalAnalyzer
from security.security_manager import SecurityManager, SecurityConfig
from error_handling.error_manager import ErrorManager, ErrorSeverity, ErrorCategory, error_handler, ErrorContext
from config.settings import get_settings
from config.logging_config import get_logger

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
        
        app.state.analyzer = AdvancedTechnicalAnalyzer()
        
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

@app.get("/api/analysis/{symbol}",
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_ip: str = "unknown") -> None:
    await manager.connect(websocket, client_ip)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_personal_message("pong", websocket)
            elif data == "stats":
                stats = manager.get_connection_stats()
                await manager.send_personal_message(json.dumps(stats), websocket)
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
                analysis_data = await api.get_batch_analysis(settings.ANALYSIS_SYMBOLS[:5])
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
         summary="종목별 뉴스 조회 (향상된)",
         description="특정 종목에 관련된 뉴스를 조회합니다.",
         response_model=List[NewsResponse],
         responses={
             200: {"description": "성공적으로 뉴스를 조회했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": EnhancedErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def get_stock_news_enhanced(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    include_korean: bool = Query(False, description="한국어 뉴스 포함 여부"),
    auto_translate: bool = Query(True, description="자동 번역 여부"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> List[NewsResponse]:
    try:
        news = api.news_collector.get_stock_news(symbol.upper(), include_korean=include_korean, auto_translate=auto_translate)
        return [NewsResponse(**item) for item in news]
    except Exception as e:
        error_id = api.error_manager.log_error(
            ErrorSeverity.MEDIUM,
            ErrorCategory.API,
            f"뉴스 조회 오류: {symbol} - {str(e)}",
            e
        )
        logger.error(f"뉴스 조회 오류: {symbol}, 오류 ID: {error_id}, 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 조회 오류. 오류 ID: {error_id}"
        )

@app.get("/api/news",
         summary="뉴스 검색 (향상된)",
         description="키워드로 뉴스를 검색합니다.",
         response_model=List[NewsResponse],
         responses={
             200: {"description": "성공적으로 뉴스를 검색했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": EnhancedErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def search_news_enhanced(
    query: str = Query(..., description="검색 키워드", example="Apple"),
    language: str = Query("en", description="언어 (en/ko)", example="en"),
    max_results: int = Query(20, description="최대 결과 수", ge=1, le=100),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> List[NewsResponse]:
    try:
        news = api.news_collector.search_news(query, language=language, max_results=max_results)
        return [NewsResponse(**item) for item in news]
    except Exception as e:
        error_id = api.error_manager.log_error(
            ErrorSeverity.MEDIUM,
            ErrorCategory.API,
            f"뉴스 검색 오류: {str(e)}",
            e
        )
        logger.error(f"뉴스 검색 오류: {query}, 오류 ID: {error_id}, 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 검색 오류. 오류 ID: {error_id}"
        )

@app.get("/api/news/multiple",
         summary="다중 종목 뉴스 조회 (향상된)",
         description="여러 종목의 뉴스를 한번에 조회합니다.",
         responses={
             200: {"description": "성공적으로 뉴스를 조회했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": EnhancedErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def get_multiple_stock_news_enhanced(
    symbols: str = Query(..., description="종목 심볼들 (쉼표로 구분)", example="AAPL,GOOGL,MSFT"),
    include_korean: bool = Query(False, description="한국어 뉴스 포함 여부"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> Dict[str, List[NewsResponse]]:
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        if len(symbol_list) > 10:
            raise HTTPException(
                status_code=400,
                detail="요청당 최대 10개 종목까지 허용됩니다"
            )
        news_dict = api.news_collector.get_multiple_stock_news(symbol_list, include_korean=include_korean)
        return {
            symbol: [NewsResponse(**item) for item in news_list]
            for symbol, news_list in news_dict.items()
        }
    except HTTPException:
        raise
    except Exception as e:
        error_id = api.error_manager.log_error(
            ErrorSeverity.MEDIUM,
            ErrorCategory.API,
            f"다중 종목 뉴스 조회 오류: {str(e)}",
            e
        )
        logger.error(f"다중 종목 뉴스 조회 오류: {str(e)}, 오류 ID: {error_id}")
        raise HTTPException(
            status_code=500,
            detail=f"다중 종목 뉴스 조회 오류. 오류 ID: {error_id}"
        )

@app.get("/api/news/detail/{news_id}",
         summary="뉴스 상세보기 (향상된)",
         description="뉴스 ID로 상세 정보를 조회합니다.",
         response_model=NewsResponse,
         responses={
             200: {"description": "성공적으로 뉴스를 조회했습니다."},
             404: {"description": "뉴스를 찾을 수 없습니다.", "model": EnhancedErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": EnhancedErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def get_news_detail_enhanced(
    news_id: str = Path(..., description="뉴스 ID (URL 인코딩)"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> NewsResponse:
    try:
        import urllib.parse
        decoded_url = urllib.parse.unquote(news_id)
        
        news = api.news_collector.get_news_by_url(decoded_url)
        if not news:
            raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")
        
        return NewsResponse(**news)
    except HTTPException:
        raise
    except Exception as e:
        error_id = api.error_manager.log_error(
            ErrorSeverity.MEDIUM,
            ErrorCategory.API,
            f"뉴스 상세 조회 오류: {str(e)}",
            e
        )
        logger.error(f"뉴스 상세 조회 오류: {news_id}, 오류 ID: {error_id}, 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 상세 조회 오류. 오류 ID: {error_id}"
        )

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info",
        access_log=True
    )
