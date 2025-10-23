from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import uvicorn

from data_collectors.stock_data_collector import StockDataCollector
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService, AlertManager
from config.settings import settings

class StockDataResponse(BaseModel):
    symbol: str = Field(..., description="주식 심볼", example="AAPL")
    price: float = Field(..., description="현재 가격", example=150.25)
    volume: int = Field(..., description="거래량", example=1000000)
    change_percent: float = Field(..., description="변동률 (%)", example=2.5)
    timestamp: datetime = Field(..., description="데이터 수집 시간")

class TechnicalAnalysisResponse(BaseModel):
    symbol: str = Field(..., description="주식 심볼")
    current_price: float = Field(..., description="현재 가격")
    trend: str = Field(..., description="트렌드 (bullish/bearish/neutral)")
    trend_strength: float = Field(..., description="트렌드 강도 (0-1)")
    signals: Dict = Field(..., description="매매 신호")
    anomalies: List[Dict] = Field(..., description="이상 패턴 목록")
    timestamp: datetime = Field(..., description="분석 시간")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="오류 메시지")
    detail: str = Field(..., description="상세 오류 정보")

app = FastAPI(
    title="Stock Analysis API",
    version="1.0.0",
    description="실시간 주식 데이터 수집 및 기술적 분석 API",
    contact={
        "name": "Stock Analysis Team",
        "email": "contact@stockanalysis.com"
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

class StockAnalysisAPI:
    def __init__(self):
        self.symbols = settings.ANALYSIS_SYMBOLS
        self.collector = StockDataCollector(
            self.symbols, 
            use_mock_data=settings.USE_MOCK_DATA,
            use_alpha_vantage=True
        )
        self.analyzer = TechnicalAnalyzer()
        
        email_config = {
            'smtp_server': settings.EMAIL_SMTP_SERVER,
            'smtp_port': settings.EMAIL_SMTP_PORT,
            'user': settings.EMAIL_USER,
            'password': settings.EMAIL_PASSWORD
        }
        
        self.notification_service = NotificationService(
            email_config=email_config,
            slack_webhook=settings.SLACK_WEBHOOK_URL
        )
        
        self.alert_manager = AlertManager(self.notification_service)

    def _load_historical_data(self, symbol: str):
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(start=datetime.now() - pd.Timedelta(days=30), end=datetime.now(), freq='D')
        np.random.seed(hash(symbol) % 2**32)
        
        base_price = 100 + hash(symbol) % 200
        price_changes = np.random.randn(len(dates)) * 2
        prices = base_price + np.cumsum(price_changes)
        
        return pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })

    async def get_realtime_data(self, symbol: str) -> Dict:
        try:
            data = self.collector.get_realtime_data(symbol)
            if not data:
                raise HTTPException(status_code=404, detail=f"Data not found for symbol: {symbol}")
            return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_analysis(self, symbol: str) -> Dict:
        try:
            realtime_data = await self.get_realtime_data(symbol)
            historical_data = self._load_historical_data(symbol)
            
            if historical_data.empty:
                raise HTTPException(status_code=404, detail=f"Historical data not found for symbol: {symbol}")
            
            analyzed_data = self.analyzer.calculate_all_indicators(historical_data)
            trend_analysis = self.analyzer.analyze_trend(analyzed_data)
            anomalies = self.analyzer.detect_anomalies(analyzed_data, symbol)
            signals = self.analyzer.generate_signals(analyzed_data, symbol)
            
            return {
                'symbol': symbol,
                'current_price': realtime_data['price'],
                'volume': realtime_data.get('volume', 0),
                'change_percent': realtime_data.get('change_percent', 0),
                'trend': trend_analysis['trend'],
                'trend_strength': trend_analysis['strength'],
                'signals': signals,
                'anomalies': anomalies,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_historical_data(self, symbol: str, days: int = 30) -> Dict:
        try:
            historical_data = self._load_historical_data(symbol)
            analyzed_data = self.analyzer.calculate_all_indicators(historical_data)
            
            chart_data = []
            for i, row in analyzed_data.iterrows():
                chart_data.append({
                    'date': row['date'].isoformat(),
                    'close': float(row['close']),
                    'volume': int(row['volume']),
                    'rsi': float(row.get('rsi', 0)) if 'rsi' in row else None,
                    'macd': float(row.get('macd', 0)) if 'macd' in row else None,
                    'bb_upper': float(row.get('bb_upper', 0)) if 'bb_upper' in row else None,
                    'bb_lower': float(row.get('bb_lower', 0)) if 'bb_lower' in row else None,
                    'sma_20': float(row.get('sma_20', 0)) if 'sma_20' in row else None
                })
            
            return {
                'symbol': symbol,
                'data': chart_data,
                'period': days
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_all_symbols_analysis(self) -> List[Dict]:
        try:
            results = []
            for symbol in self.symbols:
                try:
                    analysis = await self.get_analysis(symbol)
                    results.append(analysis)
                except Exception as e:
                    logging.error(f"Error analyzing {symbol}: {str(e)}")
                    continue
            return results
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

stock_api = StockAnalysisAPI()

@app.get("/", 
         summary="API 서버 정보",
         description="Stock Analysis API 서버의 기본 정보를 반환합니다.")
async def root():
    return {"message": "Stock Analysis API Server", "version": "1.0.0"}

@app.get("/api/health",
         summary="헬스 체크",
         description="API 서버의 상태를 확인합니다.",
         response_model=Dict[str, str])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/symbols",
         summary="분석 가능한 종목 목록",
         description="현재 분석 중인 주식 종목들의 목록을 반환합니다.",
         response_model=Dict[str, List[str]])
async def get_symbols():
    return {"symbols": settings.ANALYSIS_SYMBOLS}

@app.get("/api/realtime/{symbol}",
         summary="실시간 주가 데이터",
         description="특정 종목의 실시간 주가 정보를 조회합니다.",
         response_model=StockDataResponse,
         responses={
             200: {"description": "성공적으로 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_realtime_data(
    symbol: str = Path(..., description="주식 심볼", example="AAPL")
):
    return await stock_api.get_realtime_data(symbol)

@app.get("/api/analysis/{symbol}",
         summary="기술적 분석 결과",
         description="특정 종목의 기술적 분석 결과를 조회합니다.",
         response_model=TechnicalAnalysisResponse,
         responses={
             200: {"description": "성공적으로 분석 결과를 조회했습니다."},
             404: {"description": "해당 종목의 분석 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_analysis(
    symbol: str = Path(..., description="주식 심볼", example="AAPL")
):
    return await stock_api.get_analysis(symbol)

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
    days: int = Query(30, description="조회할 일수", ge=1, le=365)
):
    return await stock_api.get_historical_data(symbol, days)

@app.get("/api/analysis/all",
         summary="전체 종목 분석 결과",
         description="모든 분석 중인 종목의 기술적 분석 결과를 조회합니다.",
         response_model=List[TechnicalAnalysisResponse],
         responses={
             200: {"description": "성공적으로 모든 분석 결과를 조회했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_all_analysis():
    return await stock_api.get_all_symbols_analysis()

@app.get("/api/alpha-vantage/search/{keywords}",
         summary="Alpha Vantage 종목 검색",
         description="Alpha Vantage API를 사용하여 종목을 검색합니다.",
         responses={
             200: {"description": "성공적으로 종목을 검색했습니다."},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def search_symbols(
    keywords: str = Path(..., description="검색 키워드", example="Apple")
):
    return stock_api.collector.search_alpha_vantage_symbols(keywords)

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
    outputsize: str = Query("compact", description="출력 크기", example="compact")
):
    data = stock_api.collector.get_alpha_vantage_intraday_data(symbol, interval, outputsize)
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Intraday data not found for symbol: {symbol}")
    return data.to_dict('records')

@app.get("/api/alpha-vantage/weekly/{symbol}",
         summary="Alpha Vantage 주별 데이터",
         description="Alpha Vantage API를 사용하여 주별 주가 데이터를 조회합니다.",
         responses={
             200: {"description": "성공적으로 주별 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_alpha_vantage_weekly(
    symbol: str = Path(..., description="주식 심볼", example="AAPL")
):
    data = stock_api.collector.get_alpha_vantage_weekly_data(symbol)
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Weekly data not found for symbol: {symbol}")
    return data.to_dict('records')

@app.get("/api/alpha-vantage/monthly/{symbol}",
         summary="Alpha Vantage 월별 데이터",
         description="Alpha Vantage API를 사용하여 월별 주가 데이터를 조회합니다.",
         responses={
             200: {"description": "성공적으로 월별 데이터를 조회했습니다."},
             404: {"description": "해당 종목의 데이터를 찾을 수 없습니다.", "model": ErrorResponse},
             500: {"description": "서버 내부 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def get_alpha_vantage_monthly(
    symbol: str = Path(..., description="주식 심볼", example="AAPL")
):
    data = stock_api.collector.get_alpha_vantage_monthly_data(symbol)
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Monthly data not found for symbol: {symbol}")
    return data.to_dict('records')

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            analysis_data = await stock_api.get_all_symbols_analysis()
            await websocket.send_text(json.dumps(analysis_data))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/notifications/email",
         summary="이메일 발송",
         description="AI 분석 결과를 포함한 이메일을 발송합니다.",
         responses={
             200: {"description": "이메일이 성공적으로 발송되었습니다."},
             500: {"description": "이메일 발송 중 오류가 발생했습니다.", "model": ErrorResponse}
         })
async def send_email_notification(
    to_email: str = Query(..., description="수신자 이메일"),
    subject: str = Query(..., description="이메일 제목"),
    body: str = Query(..., description="이메일 내용")
):
    try:
        success = stock_api.notification_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )
        
        if success:
            return {"success": True, "message": "이메일이 성공적으로 발송되었습니다."}
        else:
            return {"success": False, "message": "이메일 발송에 실패했습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
