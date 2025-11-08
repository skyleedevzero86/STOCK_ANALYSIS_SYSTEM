from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Protocol, TypedDict, List, Dict, Optional, Union, Any
import asyncio
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
import uvicorn
import time
import hashlib
import hmac
from contextlib import asynccontextmanager

from data_collectors.performance_optimized_collector import PerformanceOptimizedCollector
from data_collectors.news_collector import NewsCollector
from analysis_engine.advanced_analyzer import AdvancedTechnicalAnalyzer
from security.security_manager import SecurityManager, SecurityConfig, security_required
from error_handling.error_manager import ErrorManager, ErrorSeverity, ErrorCategory, error_handler
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

class StockDataResponse(BaseModel):
    symbol: str = Field(..., description="주식 심볼", example="AAPL")
    currentPrice: float = Field(..., description="현재 가격", example=150.25, alias="price")
    volume: int = Field(..., description="거래량", example=1000000)
    changePercent: float = Field(..., description="변동률 (%)", example=2.5, alias="change_percent")
    timestamp: datetime = Field(..., description="데이터 수집 시간")
    confidenceScore: float = Field(..., description="데이터 신뢰도", example=0.95, alias="confidence_score")

class AdvancedAnalysisResponse(BaseModel):
    symbol: str = Field(..., description="주식 심볼")
    currentPrice: float = Field(..., description="현재 가격", alias="current_price")
    volume: int = Field(..., description="거래량")
    changePercent: float = Field(..., description="변동률", alias="change_percent")
    trend: str = Field(..., description="트렌드 (bullish/bearish/neutral)")
    trendStrength: float = Field(..., description="트렌드 강도 (0-1)", alias="trend_strength")
    marketRegime: str = Field(..., description="시장 상황", alias="market_regime")
    signals: Dict = Field(..., description="매매 신호")
    patterns: List[Dict] = Field(..., description="차트 패턴")
    supportResistance: Dict = Field(..., description="지지/저항선", alias="support_resistance")
    fibonacciLevels: Dict = Field(..., description="피보나치 레벨", alias="fibonacci_levels")
    anomalies: List[Dict] = Field(..., description="이상 패턴 목록")
    riskScore: float = Field(..., description="리스크 점수 (0-1)", alias="risk_score")
    confidence: float = Field(..., description="분석 신뢰도 (0-1)")
    timestamp: datetime = Field(..., description="분석 시간")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="오류 메시지")
    error_id: str = Field(..., description="오류 ID")
    detail: str = Field(..., description="상세 오류 정보")
    timestamp: datetime = Field(..., description="오류 발생 시간")

class PerformanceMetrics(BaseModel):
    cache_hit_rate: float
    avg_response_time: float
    error_rate: float
    active_connections: int
    queue_size: int
    memory_usage: float
    cpu_usage: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Initializing services")
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
        logger.error("Application startup error", error=str(e), exc_info=True)
        raise
    finally:
        logger.info("Application shutdown: Cleaning up")
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.stockanalysis.com"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.rate_limits: Dict[str, float] = {}
        
    async def connect(self, websocket: WebSocket, client_ip: str) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[websocket] = {
            'client_ip': client_ip,
            'connected_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'message_count': 0
        }
        logger.info("WebSocket connection established", client_ip=client_ip)
        
    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata.pop(websocket)
            logger.info("WebSocket connection closed", client_ip=metadata.get('client_ip'))
    
    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        try:
            await websocket.send_text(message)
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]['last_activity'] = datetime.utcnow()
                self.connection_metadata[websocket]['message_count'] += 1
        except Exception as e:
            logger.error("Error sending WebSocket message", error=str(e))
            self.disconnect(websocket)
    
    async def broadcast(self, message: str) -> None:
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        if not self.connection_metadata:
            return {
                'active_connections': 0,
                'total_messages': 0,
                'avg_connection_duration': 0.0
            }
        
        total_duration = sum(
            (datetime.utcnow() - meta['connected_at']).total_seconds()
            for meta in self.connection_metadata.values()
        )
        
        return {
            'active_connections': len(self.active_connections),
            'total_messages': sum(meta['message_count'] for meta in self.connection_metadata.values()),
            'avg_connection_duration': total_duration / len(self.connection_metadata)
        }

manager = ConnectionManager()

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
        """
        실시간 주식 데이터를 조회합니다.
        
        Args:
            symbol: 주식 심볼 (예: 'AAPL')
            
        Returns:
            Dict[str, Any]: 실시간 주가 정보를 포함한 딕셔너리
            
        Raises:
            HTTPException: 데이터를 찾을 수 없거나 오류가 발생한 경우
        """
        try:
            start_time = time.time()
            data = await self.data_collector.get_realtime_data_async(symbol)
            
            if not data or data.get('price', 0) <= 0:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Data not found for symbol: {symbol}"
                )
            
            response_time = time.time() - start_time
            confidence_score = min(1.0, max(0.0, 1.0 - (response_time / 5.0)))
            
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
            error_id = self.error_manager.log_error(
                ErrorSeverity.HIGH,
                ErrorCategory.DATA_COLLECTION,
                f"Error fetching realtime data for {symbol}: {str(e)}",
                e
            )
            logger.error("Error fetching realtime data", symbol=symbol, error=str(e), error_id=error_id)
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error. Error ID: {error_id}"
            )
    
    async def get_advanced_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        고급 기술적 분석을 수행합니다.
        
        Args:
            symbol: 주식 심볼 (예: 'AAPL')
            
        Returns:
            Dict[str, Any]: 분석 결과를 포함한 딕셔너리
            
        Raises:
            HTTPException: 데이터를 찾을 수 없거나 오류가 발생한 경우
        """
        try:
            realtime_data = await self.get_realtime_data_enhanced(symbol)
            historical_data = await self.data_collector.get_historical_data_async(symbol, "3mo")
            
            if historical_data.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"Historical data not found for symbol: {symbol}"
                )
            
            analyzed_data = self.analyzer.calculate_all_advanced_indicators(historical_data)
            
            market_regime = self.analyzer.calculate_market_regime(analyzed_data)
            patterns = self.analyzer.detect_chart_patterns(analyzed_data)
            support_resistance = self.analyzer.calculate_support_resistance(analyzed_data)
            fibonacci_levels = self.analyzer.calculate_fibonacci_levels(analyzed_data)
            anomalies = self.analyzer.detect_anomalies_ml(analyzed_data)
            signals = self.analyzer.calculate_advanced_signals(analyzed_data)
            
            risk_score = self._calculate_risk_score(analyzed_data, anomalies)
            confidence = self._calculate_analysis_confidence(analyzed_data, market_regime)
            
            return {
                'symbol': symbol,
                'currentPrice': realtime_data['currentPrice'],
                'volume': realtime_data.get('volume', 0),
                'changePercent': realtime_data.get('changePercent', 0),
                'trend': signals['signal'],
                'trendStrength': signals['confidence'],
                'marketRegime': market_regime['regime'],
                'signals': signals,
                'patterns': patterns,
                'supportResistance': support_resistance,
                'fibonacciLevels': fibonacci_levels,
                'anomalies': [
                    {
                        'type': anomaly['type'],
                        'severity': anomaly['severity'],
                        'message': anomaly.get('message', f"Anomaly detected: {anomaly['type']}"),
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
                f"Error in advanced analysis for {symbol}: {str(e)}",
                e
            )
            logger.error("Error in advanced analysis", symbol=symbol, error=str(e), error_id=error_id)
            raise HTTPException(
                status_code=500,
                detail=f"Analysis error. Error ID: {error_id}"
            )
    
    def _calculate_risk_score(self, data: pd.DataFrame, anomalies: List[Dict[str, Any]]) -> float:
        """
        리스크 점수를 계산합니다.
        
        Args:
            data: 분석된 주가 데이터
            anomalies: 감지된 이상 패턴 목록
            
        Returns:
            float: 0.0에서 1.0 사이의 리스크 점수
        """
        base_risk = 0.1
        
        if len(anomalies) > 0:
            base_risk += min(0.4, len(anomalies) * 0.1)
        
        if 'close' in data.columns and len(data) > 1:
            volatility = data['close'].pct_change().std()
            if pd.notna(volatility):
                base_risk += min(0.3, float(volatility) * 10)
        
        return min(1.0, base_risk)
    
    def _calculate_analysis_confidence(self, data: pd.DataFrame, market_regime: Dict[str, Any]) -> float:
        """
        분석 신뢰도를 계산합니다.
        
        Args:
            data: 분석된 주가 데이터
            market_regime: 시장 상황 정보
            
        Returns:
            float: 0.0에서 1.0 사이의 신뢰도 점수
        """
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
        """
        여러 종목에 대한 배치 분석을 수행합니다.
        
        Args:
            symbols: 분석할 주식 심볼 목록
            
        Returns:
            List[Dict[str, Any]]: 각 종목의 분석 결과 목록
        """
        try:
            tasks = [self.get_advanced_analysis(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error("Error analyzing symbol", symbol=symbols[i], error=str(result))
                    continue
                if result:
                    valid_results.append(result)
            
            return valid_results
            
        except Exception as e:
            error_id = self.error_manager.log_error(
                ErrorSeverity.MEDIUM,
                ErrorCategory.ANALYSIS,
                f"Error in batch analysis: {str(e)}",
                e
            )
            logger.error("Error in batch analysis", error=str(e), error_id=error_id)
            raise HTTPException(
                status_code=500,
                detail=f"Batch analysis error. Error ID: {error_id}"
            )

def get_stock_api(request: Request) -> StockAnalysisAPI:
    """
    의존성 주입을 위한 StockAnalysisAPI 인스턴스를 생성합니다.
    
    Args:
        request: FastAPI Request 객체
        
    Returns:
        StockAnalysisAPI: 초기화된 API 인스턴스
    """
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
    """
    API 서버의 기본 정보를 반환합니다.
    
    Returns:
        Dict[str, Any]: 서버 정보 및 기능 목록
    """
    return {
        "message": "Enhanced Stock Analysis API Server", 
        "version": "2.0.0",
        "features": [
            "Advanced technical analysis",
            "Real-time data streaming",
            "Performance optimization",
            "Enhanced security",
            "Comprehensive error handling"
        ]
    }

@app.get("/api/health",
         summary="헬스 체크",
         description="API 서버의 상태를 확인합니다.",
         response_model=Dict[str, Union[str, float]])
async def health_check(api: StockAnalysisAPI = Depends(get_stock_api)) -> Dict[str, Any]:
    """
    API 서버의 헬스 상태를 확인합니다.
    
    Args:
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        Dict[str, Any]: 헬스 체크 결과
    """
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
        logger.error("Health check failed", error=str(e))
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
    """
    API 서버의 성능 메트릭을 조회합니다.
    
    Args:
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        PerformanceMetrics: 성능 지표
    """
    metrics = api.data_collector.get_performance_metrics()
    return PerformanceMetrics(**metrics)

@app.get("/api/realtime/{symbol}",
         summary="실시간 주가 데이터 (향상된)",
         description="특정 종목의 실시간 주가 정보를 조회합니다.",
         response_model=StockDataResponse,
         responses={
             200: {"description": "성공적으로 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def get_realtime_data(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> StockDataResponse:
    """
    실시간 주가 데이터를 조회합니다.
    
    Args:
        symbol: 주식 심볼
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        StockDataResponse: 실시간 주가 정보
    """
    result = await api.get_realtime_data_enhanced(symbol)
    return StockDataResponse(**result)

@app.get("/api/analysis/{symbol}",
         summary="고급 기술적 분석 결과",
         description="특정 종목의 고급 기술적 분석 결과를 조회합니다.",
         response_model=AdvancedAnalysisResponse,
         responses={
             200: {"description": "성공적으로 분석 결과를 조회했습니다."},
             404: {"description": "해당 종목의 분석 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
@error_handler(ErrorSeverity.HIGH, ErrorCategory.ANALYSIS)
async def get_advanced_analysis(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> AdvancedAnalysisResponse:
    """
    고급 기술적 분석 결과를 조회합니다.
    
    Args:
        symbol: 주식 심볼
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        AdvancedAnalysisResponse: 분석 결과
    """
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
    """
    여러 종목에 대한 배치 분석을 수행합니다.
    
    Args:
        symbols: 쉼표로 구분된 주식 심볼 목록
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        List[AdvancedAnalysisResponse]: 각 종목의 분석 결과 목록
    """
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    if len(symbol_list) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 symbols allowed per batch request"
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
    """
    시스템 오류 통계를 조회합니다.
    
    Args:
        hours: 조회할 시간 범위 (시간)
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        Dict[str, Any]: 오류 통계 정보
    """
    return api.error_manager.get_error_statistics(hours=hours)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_ip: str = "unknown") -> None:
    """
    WebSocket 연결을 처리합니다.
    
    Args:
        websocket: WebSocket 연결 객체
        client_ip: 클라이언트 IP 주소
    """
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
    """
    실시간 데이터를 WebSocket으로 스트리밍합니다.
    
    Args:
        websocket: WebSocket 연결 객체
        client_ip: 클라이언트 IP 주소
    """
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
                logger.error("WebSocket streaming error", error=str(e))
                await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP 예외를 처리합니다.
    
    Args:
        request: FastAPI Request 객체
        exc: HTTPException 객체
        
    Returns:
        JSONResponse: 오류 응답
    """
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
    """
    일반 예외를 처리합니다.
    
    Args:
        request: FastAPI Request 객체
        exc: Exception 객체
        
    Returns:
        JSONResponse: 오류 응답
    """
    error_id = f"ERR_{int(time.time())}_{hash(str(exc)) % 10000}"
    logger.error("Unhandled exception", error=str(exc), error_id=error_id, path=str(request.url))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

class NewsResponse(BaseModel):
    title: str = Field(..., description="뉴스 제목")
    description: Optional[str] = Field(None, description="뉴스 설명")
    url: str = Field(..., description="뉴스 URL")
    source: Optional[str] = Field(None, description="뉴스 출처")
    published_at: Optional[str] = Field(None, description="발행 시간")
    symbol: str = Field(..., description="관련 종목")
    provider: str = Field(..., description="뉴스 제공자")
    sentiment: Optional[float] = Field(None, description="감성 점수")

@app.get("/api/news/{symbol}",
         summary="종목별 뉴스 조회 (향상된)",
         description="특정 종목에 관련된 뉴스를 조회합니다.",
         response_model=List[NewsResponse],
         responses={
             200: {"description": "성공적으로 뉴스를 조회했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def get_stock_news_enhanced(
    symbol: str = Path(..., description="주식 심볼", example="AAPL"),
    include_korean: bool = Query(False, description="한국어 뉴스 포함 여부"),
    auto_translate: bool = Query(True, description="자동 번역 여부"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> List[NewsResponse]:
    """
    종목별 뉴스를 조회합니다.
    
    Args:
        symbol: 주식 심볼
        include_korean: 한국어 뉴스 포함 여부
        auto_translate: 자동 번역 여부
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        List[NewsResponse]: 뉴스 목록
    """
    try:
        news = api.news_collector.get_stock_news(symbol.upper(), include_korean=include_korean, auto_translate=auto_translate)
        return [NewsResponse(**item) for item in news]
    except Exception as e:
        error_id = api.error_manager.log_error(
            ErrorSeverity.MEDIUM,
            ErrorCategory.API,
            f"Error fetching news for {symbol}: {str(e)}",
            e
        )
        logger.error("Error fetching news", symbol=symbol, error=str(e), error_id=error_id)
        raise HTTPException(
            status_code=500,
            detail=f"News fetch error. Error ID: {error_id}"
        )

@app.get("/api/news",
         summary="뉴스 검색 (향상된)",
         description="키워드로 뉴스를 검색합니다.",
         response_model=List[NewsResponse],
         responses={
             200: {"description": "성공적으로 뉴스를 검색했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def search_news_enhanced(
    query: str = Query(..., description="검색 키워드", example="Apple"),
    language: str = Query("en", description="언어 (en/ko)", example="en"),
    max_results: int = Query(20, description="최대 결과 수", ge=1, le=100),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> List[NewsResponse]:
    """
    키워드로 뉴스를 검색합니다.
    
    Args:
        query: 검색 키워드
        language: 언어 코드
        max_results: 최대 결과 수
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        List[NewsResponse]: 검색된 뉴스 목록
    """
    try:
        news = api.news_collector.search_news(query, language=language, max_results=max_results)
        return [NewsResponse(**item) for item in news]
    except Exception as e:
        error_id = api.error_manager.log_error(
            ErrorSeverity.MEDIUM,
            ErrorCategory.API,
            f"Error searching news: {str(e)}",
            e
        )
        logger.error("Error searching news", query=query, error=str(e), error_id=error_id)
        raise HTTPException(
            status_code=500,
            detail=f"News search error. Error ID: {error_id}"
        )

@app.get("/api/news/multiple",
         summary="다중 종목 뉴스 조회 (향상된)",
         description="여러 종목의 뉴스를 한번에 조회합니다.",
         responses={
             200: {"description": "성공적으로 뉴스를 조회했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def get_multiple_stock_news_enhanced(
    symbols: str = Query(..., description="종목 심볼들 (쉼표로 구분)", example="AAPL,GOOGL,MSFT"),
    include_korean: bool = Query(False, description="한국어 뉴스 포함 여부"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> Dict[str, List[NewsResponse]]:
    """
    여러 종목의 뉴스를 한번에 조회합니다.
    
    Args:
        symbols: 쉼표로 구분된 주식 심볼 목록
        include_korean: 한국어 뉴스 포함 여부
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        Dict[str, List[NewsResponse]]: 종목별 뉴스 목록
    """
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
        error_id = api.error_manager.log_error(
            ErrorSeverity.MEDIUM,
            ErrorCategory.API,
            f"Error fetching multiple stock news: {str(e)}",
            e
        )
        logger.error("Error fetching multiple stock news", error=str(e), error_id=error_id)
        raise HTTPException(
            status_code=500,
            detail=f"Multiple stock news fetch error. Error ID: {error_id}"
        )

@app.get("/api/news/detail/{news_id}",
         summary="뉴스 상세보기 (향상된)",
         description="뉴스 ID로 상세 정보를 조회합니다.",
         response_model=NewsResponse,
         responses={
             200: {"description": "성공적으로 뉴스를 조회했습니다."},
             404: {"description": "뉴스를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
@error_handler(ErrorSeverity.MEDIUM, ErrorCategory.API)
async def get_news_detail_enhanced(
    news_id: str = Path(..., description="뉴스 ID (URL 인코딩)"),
    api: StockAnalysisAPI = Depends(get_stock_api)
) -> NewsResponse:
    """
    뉴스 상세 정보를 조회합니다.
    
    Args:
        news_id: URL 인코딩된 뉴스 ID
        api: StockAnalysisAPI 인스턴스
        
    Returns:
        NewsResponse: 뉴스 상세 정보
    """
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
            f"Error fetching news detail: {str(e)}",
            e
        )
        logger.error("Error fetching news detail", news_id=news_id, error=str(e), error_id=error_id)
        raise HTTPException(
            status_code=500,
            detail=f"News detail fetch error. Error ID: {error_id}"
        )

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info",
        access_log=True
    )