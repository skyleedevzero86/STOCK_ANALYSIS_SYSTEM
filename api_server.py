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
    symbol: str = Field(..., example="AAPL")
    price: float = Field(..., example=150.25)
    volume: int = Field(..., example=1000000)
    change_percent: float = Field(..., example=2.5)
    timestamp: datetime

class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    trend: str
    trend_strength: float
    signals: Dict
    anomalies: List[Dict]
    timestamp: datetime

class ErrorResponse(BaseModel):
    error: str
    detail: str

app = FastAPI(
    title="Stock Analysis API",
    version="1.0.0",
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

@app.get("/")
async def root():
    return {"message": "Stock Analysis API Server", "version": "1.0.0"}

@app.get("/api/health",
         response_model=Dict[str, str])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/symbols",
         response_model=Dict[str, List[str]])
async def get_symbols():
    return {"symbols": settings.ANALYSIS_SYMBOLS}

@app.get("/api/realtime/{symbol}",
         response_model=StockDataResponse,
         responses={
             200: {"description": "Success"},
             404: {"description": "Not found", "model": ErrorResponse},
             500: {"description": "Server error", "model": ErrorResponse}
         })
async def get_realtime_data(
    symbol: str = Path(..., example="AAPL")
):
    return await stock_api.get_realtime_data(symbol)

@app.get("/api/analysis/{symbol}",
         response_model=TechnicalAnalysisResponse,
         responses={
             200: {"description": "Success"},
             404: {"description": "Not found", "model": ErrorResponse},
             500: {"description": "Server error", "model": ErrorResponse}
         })
async def get_analysis(
    symbol: str = Path(..., example="AAPL")
):
    return await stock_api.get_analysis(symbol)

@app.get("/api/historical/{symbol}",
         responses={
             200: {"description": "Success"},
             404: {"description": "Not found", "model": ErrorResponse},
             500: {"description": "Server error", "model": ErrorResponse}
         })
async def get_historical_data(
    symbol: str = Path(..., example="AAPL"),
    days: int = Query(30, ge=1, le=365)
):
    return await stock_api.get_historical_data(symbol, days)

@app.get("/api/analysis/all",
         response_model=List[TechnicalAnalysisResponse],
         responses={
             200: {"description": "Success"},
             500: {"description": "Server error", "model": ErrorResponse}
         })
async def get_all_analysis():
    return await stock_api.get_all_symbols_analysis()

@app.get("/api/alpha-vantage/search/{keywords}",
         responses={
             200: {"description": "Success"},
             500: {"description": "Server error", "model": ErrorResponse}
         })
async def search_symbols(
    keywords: str = Path(..., example="Apple")
):
    return stock_api.collector.search_alpha_vantage_symbols(keywords)

@app.get("/api/alpha-vantage/intraday/{symbol}",
         responses={
             200: {"description": "Success"},
             404: {"description": "Not found", "model": ErrorResponse},
             500: {"description": "Server error", "model": ErrorResponse}
         })
async def get_alpha_vantage_intraday(
    symbol: str = Path(..., example="AAPL"),
    interval: str = Query("5min", example="5min"),
    outputsize: str = Query("compact", example="compact")
):
    data = stock_api.collector.get_alpha_vantage_intraday_data(symbol, interval, outputsize)
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Intraday data not found for symbol: {symbol}")
    return data.to_dict('records')

@app.get("/api/alpha-vantage/weekly/{symbol}",
         responses={
             200: {"description": "Success"},
             404: {"description": "Not found", "model": ErrorResponse},
             500: {"description": "Server error", "model": ErrorResponse}
         })
async def get_alpha_vantage_weekly(
    symbol: str = Path(..., example="AAPL")
):
    data = stock_api.collector.get_alpha_vantage_weekly_data(symbol)
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Weekly data not found for symbol: {symbol}")
    return data.to_dict('records')

@app.get("/api/alpha-vantage/monthly/{symbol}",
         responses={
             200: {"description": "Success"},
             404: {"description": "Not found", "model": ErrorResponse},
             500: {"description": "Server error", "model": ErrorResponse}
         })
async def get_alpha_vantage_monthly(
    symbol: str = Path(..., example="AAPL")
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
         responses={
             200: {"description": "Success"},
             500: {"description": "Server error", "model": ErrorResponse}
         })
async def send_email_notification(
    to_email: str = Query(...),
    subject: str = Query(...),
    body: str = Query(...)
):
    try:
        success = stock_api.notification_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )
        
        if success:
            return {"success": True, "message": "Email sent successfully"}
        else:
            return {"success": False, "message": "Email sending failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
