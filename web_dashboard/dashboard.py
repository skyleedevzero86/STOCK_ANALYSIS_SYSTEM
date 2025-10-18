import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, List
import time

st.set_page_config(
    page_title="실시간 주식 분석 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class StockDashboard:
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        
    def load_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        dates = pd.date_range(start=datetime.now() - timedelta(days=days), end=datetime.now(), freq='D')
        np.random.seed(hash(symbol) % 2**32)
        
        base_price = 100 + hash(symbol) % 200
        price_changes = np.random.randn(len(dates)) * 2
        prices = base_price + np.cumsum(price_changes)
        
        volumes = np.random.randint(1000000, 5000000, len(dates))
        
        data = pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': volumes,
            'symbol': symbol
        })
        
        return data
    
    def create_price_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['date'],
            y=data['close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#1f77b4', width=2)
        ))
        
        if len(data) >= 20:
            sma_20 = data['close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=sma_20,
                mode='lines',
                name='SMA 20',
                line=dict(color='orange', width=1, dash='dash')
            ))
        
        fig.update_layout(
            title=f"{symbol} 주가 차트",
            xaxis_title="날짜",
            yaxis_title="가격 ($)",
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    def create_volume_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=data['date'],
            y=data['volume'],
            name='Volume',
            marker_color='lightblue'
        ))
        
        fig.update_layout(
            title=f"{symbol} 거래량",
            xaxis_title="날짜",
            yaxis_title="거래량",
            template='plotly_white'
        )
        
        return fig
    
    def create_technical_indicators(self, data: pd.DataFrame) -> Dict:
        if len(data) < 20:
            return {}
        
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        ema_12 = data['close'].ewm(span=12).mean()
        ema_26 = data['close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        macd_histogram = macd - macd_signal
        
        sma_20 = data['close'].rolling(window=20).mean()
        std_20 = data['close'].rolling(window=20).std()
        bb_upper = sma_20 + (std_20 * 2)
        bb_lower = sma_20 - (std_20 * 2)
        
        return {
            'rsi': rsi.iloc[-1] if not rsi.empty else 0,
            'macd': macd.iloc[-1] if not macd.empty else 0,
            'macd_signal': macd_signal.iloc[-1] if not macd_signal.empty else 0,
            'bb_upper': bb_upper.iloc[-1] if not bb_upper.empty else 0,
            'bb_middle': sma_20.iloc[-1] if not sma_20.empty else 0,
            'bb_lower': bb_lower.iloc[-1] if not bb_lower.empty else 0
        }
    
    def create_indicators_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['date'],
            y=data['close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#1f77b4', width=2)
        ))
        
        if len(data) >= 20:
            sma_20 = data['close'].rolling(window=20).mean()
            std_20 = data['close'].rolling(window=20).std()
            bb_upper = sma_20 + (std_20 * 2)
            bb_lower = sma_20 - (std_20 * 2)
            
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=bb_upper,
                mode='lines',
                name='BB Upper',
                line=dict(color='red', width=1, dash='dot'),
                fill=None
            ))
            
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=bb_lower,
                mode='lines',
                name='BB Lower',
                line=dict(color='red', width=1, dash='dot'),
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.1)'
            ))
            
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=sma_20,
                mode='lines',
                name='SMA 20',
                line=dict(color='orange', width=1, dash='dash')
            ))
        
        fig.update_layout(
            title=f"{symbol} 기술적 지표",
            xaxis_title="날짜",
            yaxis_title="가격 ($)",
            template='plotly_white'
        )
        
        return fig
    
    def display_summary_cards(self, data: pd.DataFrame, indicators: Dict):
        if data.empty:
            return
        
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        
        price_change = latest['close'] - prev['close']
        price_change_pct = (price_change / prev['close']) * 100
        
        volume_change = latest['volume'] - prev['volume'] if len(data) > 1 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="현재가",
                value=f"${latest['close']:.2f}",
                delta=f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
            )
        
        with col2:
            st.metric(
                label="거래량",
                value=f"{latest['volume']:,}",
                delta=f"{volume_change:+,}"
            )
        
        with col3:
            rsi = indicators.get('rsi', 0)
            rsi_status = "과매수" if rsi > 70 else "과매도" if rsi < 30 else "정상"
            st.metric(
                label="RSI",
                value=f"{rsi:.1f}",
                delta=rsi_status
            )
        
        with col4:
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            macd_status = "상승" if macd > macd_signal else "하락"
            st.metric(
                label="MACD",
                value=f"{macd:.3f}",
                delta=macd_status
            )

def main():
    st.title("📈 실시간 주식 분석 대시보드")
    st.markdown("---")
    
    dashboard = StockDashboard()
    
    st.sidebar.title("설정")
    
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
    selected_symbol = st.sidebar.selectbox("종목 선택", symbols)
    
    days = st.sidebar.slider("분석 기간 (일)", min_value=7, max_value=365, value=30)
    
    if st.sidebar.button("🔄 새로고침"):
        st.rerun()
    
    with st.spinner("데이터를 불러오는 중..."):
        data = dashboard.load_data(selected_symbol, days)
        indicators = dashboard.create_technical_indicators(data)
    
    if data.empty:
        st.error("데이터를 불러올 수 없습니다.")
        return
    
    st.subheader("📊 주요 지표")
    dashboard.display_summary_cards(data, indicators)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 가격 차트")
        price_chart = dashboard.create_price_chart(data, selected_symbol)
        st.plotly_chart(price_chart, use_container_width=True)
    
    with col2:
        st.subheader("📊 거래량")
        volume_chart = dashboard.create_volume_chart(data, selected_symbol)
        st.plotly_chart(volume_chart, use_container_width=True)
    
    st.subheader("🔍 기술적 지표")
    indicators_chart = dashboard.create_indicators_chart(data, selected_symbol)
    st.plotly_chart(indicators_chart, use_container_width=True)
    
    st.subheader("📋 상세 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**기술적 지표**")
        if indicators:
            st.write(f"• RSI (14): {indicators.get('rsi', 0):.2f}")
            st.write(f"• MACD: {indicators.get('macd', 0):.4f}")
            st.write(f"• MACD Signal: {indicators.get('macd_signal', 0):.4f}")
            st.write(f"• 볼린저 밴드 상단: ${indicators.get('bb_upper', 0):.2f}")
            st.write(f"• 볼린저 밴드 하단: ${indicators.get('bb_lower', 0):.2f}")
    
    with col2:
        st.markdown("**거래 통계**")
        if not data.empty:
            st.write(f"• 평균 가격: ${data['close'].mean():.2f}")
            st.write(f"• 최고가: ${data['close'].max():.2f}")
            st.write(f"• 최저가: ${data['close'].min():.2f}")
            st.write(f"• 평균 거래량: {data['volume'].mean():,.0f}")
            st.write(f"• 최대 거래량: {data['volume'].max():,}")
    
    st.subheader("📄 원시 데이터")
    st.dataframe(data.tail(10), use_container_width=True)
    
    if st.sidebar.checkbox("자동 새로고침 (30초)"):
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    import numpy as np
    main()
