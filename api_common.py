from fastapi import WebSocket
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from datetime import datetime
import logging

class StockDataResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    symbol: str = Field(..., description="주식 심볼", example="AAPL")
    currentPrice: float = Field(..., description="현재 가격", example=150.25, alias="price")
    volume: int = Field(..., description="거래량", example=1000000)
    changePercent: float = Field(..., description="변동률 (%)", example=2.5, alias="change_percent")
    timestamp: datetime = Field(..., description="데이터 수집 시간")
    confidenceScore: Optional[float] = Field(None, description="데이터 신뢰도", example=0.95, alias="confidence_score")

class TradingSignalsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    signal: str = Field(..., description="매매 신호")
    confidence: float = Field(..., description="신뢰도")
    rsi: Optional[float] = Field(None, description="RSI 값")
    macd: Optional[float] = Field(None, description="MACD 값")
    macdSignal: Optional[float] = Field(None, description="MACD 시그널", alias="macd_signal")

class AnomalyResponse(BaseModel):
    type: str = Field(..., description="이상 패턴 타입")
    severity: str = Field(..., description="심각도")
    message: str = Field(..., description="메시지")
    timestamp: datetime = Field(..., description="발생 시간")

class TechnicalAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    symbol: str = Field(..., description="주식 심볼")
    currentPrice: float = Field(..., description="현재 가격", alias="current_price")
    volume: int = Field(..., description="거래량")
    changePercent: float = Field(..., description="변동률", alias="change_percent")
    trend: str = Field(..., description="트렌드 (bullish/bearish/neutral)")
    trendStrength: float = Field(..., description="트렌드 강도 (0-1)", alias="trend_strength")
    signals: TradingSignalsResponse = Field(..., description="매매 신호")
    anomalies: List[AnomalyResponse] = Field(..., description="이상 패턴 목록")
    timestamp: datetime = Field(..., description="분석 시간")

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
    detail: str = Field(..., description="상세 오류 정보")

class EnhancedErrorResponse(BaseModel):
    error: str = Field(..., description="오류 메시지")
    error_id: str = Field(..., description="오류 ID")
    detail: str = Field(..., description="상세 오류 정보")
    timestamp: datetime = Field(..., description="오류 발생 시간")

class EmailNotificationRequest(BaseModel):
    to_email: str = Field(..., description="수신자 이메일")
    subject: str = Field(..., description="이메일 제목")
    body: str = Field(..., description="이메일 내용")

class EmailNotificationResponse(BaseModel):
    success: bool = Field(..., description="발송 성공 여부")
    message: str = Field(..., description="응답 메시지")

class SmsNotificationRequest(BaseModel):
    from_phone: str = Field(..., description="발신번호 (01012345678 형식)")
    to_phone: str = Field(..., description="수신번호 (01012345678 형식)")
    message: str = Field(..., description="메시지 내용")

class SmsNotificationResponse(BaseModel):
    success: bool = Field(..., description="발송 성공 여부")
    message: str = Field(..., description="응답 메시지")

class NewsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    title: str = Field(..., description="뉴스 제목")
    description: Optional[str] = Field(None, description="뉴스 설명")
    url: str = Field(..., description="뉴스 URL")
    source: Optional[str] = Field(None, description="뉴스 출처")
    published_at: Optional[str] = Field(None, description="발행 시간")
    symbol: str = Field(..., description="관련 종목")
    provider: str = Field(..., description="뉴스 제공자")
    sentiment: Optional[float] = Field(None, description="감성 점수")

class PerformanceMetrics(BaseModel):
    cache_hit_rate: float
    avg_response_time: float
    error_rate: float
    active_connections: int
    queue_size: int
    memory_usage: float
    cpu_usage: float

class ConnectionManager:
    def __init__(self, enable_metadata: bool = False):
        self.active_connections: List[WebSocket] = []
        self.enable_metadata = enable_metadata
        if enable_metadata:
            self.connection_metadata: Dict[WebSocket, Dict] = {}
            self.rate_limits: Dict[str, float] = {}
        
    async def connect(self, websocket: WebSocket, client_ip: str = "unknown") -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if self.enable_metadata:
            self.connection_metadata[websocket] = {
                'client_ip': client_ip,
                'connected_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'message_count': 0
            }
            logging.info(f"WebSocket 연결 수립됨: {client_ip}")
        
    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if self.enable_metadata and websocket in self.connection_metadata:
            metadata = self.connection_metadata.pop(websocket)
            logging.info(f"WebSocket 연결 종료됨: {metadata.get('client_ip')}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        try:
            await websocket.send_text(message)
            if self.enable_metadata and websocket in self.connection_metadata:
                self.connection_metadata[websocket]['last_activity'] = datetime.utcnow()
                self.connection_metadata[websocket]['message_count'] += 1
        except Exception as e:
            logging.error(f"WebSocket 메시지 전송 오류: {str(e)}")
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
    
    def get_connection_stats(self) -> Dict:
        if not self.enable_metadata or not self.connection_metadata:
            return {
                'active_connections': len(self.active_connections),
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
            'avg_connection_duration': total_duration / len(self.connection_metadata) if self.connection_metadata else 0.0
        }

def create_cors_middleware_config() -> Dict:
    return {
        'allow_origins': ["*"],
        'allow_credentials': True,
        'allow_methods': ["*"],
        'allow_headers': ["*"],
    }

def format_timestamp(timestamp) -> datetime:
    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return datetime.now()
    elif timestamp is None:
        return datetime.now()
    return timestamp

def safe_float(value, default=None):
    import pandas as pd
    import numpy as np
    
    if pd.isna(value) or (isinstance(value, float) and np.isnan(value)):
        return default
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


