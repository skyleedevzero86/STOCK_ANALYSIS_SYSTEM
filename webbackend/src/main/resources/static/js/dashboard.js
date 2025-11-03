class StockDashboard {
    constructor() {
        this.apiBaseUrl = "http://localhost:8080";
        this.pythonApiUrl = "http://localhost:9000";
        this.wsUrl = "ws://localhost:8080/ws/stocks";
        this.charts = {};
        this.currentSymbol = "AAPL";
        this.currentDays = 30;
        this.autoRefreshInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setupWebSocket();
    }

    setupEventListeners() {
        document.getElementById('symbolSelect').addEventListener('change', (e) => {
            this.currentSymbol = e.target.value;
            this.loadData();
        });

        const daysSlider = document.getElementById('daysSlider');
        const daysValue = document.getElementById('daysValue');
        daysSlider.addEventListener('input', (e) => {
            this.currentDays = parseInt(e.target.value);
            daysValue.textContent = this.currentDays;
        });

        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadData();
        });

        document.getElementById('autoRefresh').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        });
    }

    async loadInitialData() {
        await this.loadData();
    }

    async loadData() {
        try {
            this.showLoading();

            const realtimeResponse = await axios.get(
                `${this.apiBaseUrl}/api/stocks/realtime/${this.currentSymbol}`
            );

            const historicalResponse = await axios.get(
                `${this.apiBaseUrl}/api/stocks/historical/${this.currentSymbol}?days=${this.currentDays}`
            );

            const analysisResponse = await axios.get(
                `${this.apiBaseUrl}/api/stocks/analysis/${this.currentSymbol}`
            );

            this.updateMetrics(realtimeResponse.data, analysisResponse.data);
            this.updateCharts(historicalResponse.data);
            this.updateAnalysisDetails(analysisResponse.data);
            this.updateDataTable(historicalResponse.data);

        } catch (error) {
            console.error("데이터 로드 실패:", error);
            if (error.response) {

                console.error("서버 응답 상태:", error.response.status);
                console.error("서버 응답 데이터:", error.response.data);
                const errorMessage = error.response.data?.message || error.response.data?.error || "알 수 없는 오류";
                this.showError(`데이터를 불러올 수 없습니다: ${errorMessage}`);
            } else if (error.request) {

                console.error("서버 응답 없음:", error.request);
                this.showError("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.");
            } else {

                console.error("요청 설정 오류:", error.message);
                this.showError(`데이터를 불러올 수 없습니다: ${error.message}`);
            }
        }
    }

    setupWebSocket() {
        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                console.log("WebSocket 연결됨");
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.updateRealtimeData(data);
            };

            this.ws.onclose = () => {
                console.log("WebSocket 연결 끊어짐");
                setTimeout(() => this.setupWebSocket(), 5000);
            };

            this.ws.onerror = (error) => {
                console.error("WebSocket 오류:", error);
            };
        } catch (error) {
            console.error("WebSocket 설정 실패:", error);
        }
    }

    updateMetrics(realtimeData, analysisData) {
        document.getElementById('currentPrice').textContent = `$${realtimeData.price.toFixed(2)}`;
        document.getElementById('priceChange').textContent =
            `${realtimeData.change_percent >= 0 ? '+' : ''}${realtimeData.change_percent.toFixed(2)}%`;
        document.getElementById('priceChange').className =
            `metric-change ${realtimeData.change_percent >= 0 ? 'positive' : 'negative'}`;

        document.getElementById('volume').textContent = realtimeData.volume.toLocaleString();
        document.getElementById('volumeChange').textContent = `+${Math.floor(Math.random() * 100000)}`;

        const rsi = analysisData.signals?.rsi || 0;
        document.getElementById('rsi').textContent = rsi.toFixed(1);
        const rsiStatus = rsi > 70 ? "과매수" : rsi < 30 ? "과매도" : "정상";
        document.getElementById('rsiStatus').textContent = rsiStatus;

        const macd = analysisData.signals?.macd || 0;
        document.getElementById('macd').textContent = macd.toFixed(3);
        const macdSignal = analysisData.signals?.macd_signal || 0;
        const macdStatus = macd > macdSignal ? "상승" : "하락";
        document.getElementById('macdStatus').textContent = macdStatus;
    }

    updateCharts(historicalData) {
        if (!historicalData.data || historicalData.data.length === 0) return;

        const data = historicalData.data;
        const dates = data.map(d => d.date);
        const prices = data.map(d => d.close);
        const volumes = data.map(d => d.volume);

        const priceTrace = {
            x: dates,
            y: prices,
            type: 'scatter',
            mode: 'lines',
            name: 'Close Price',
            line: { color: '#1f77b4', width: 2 }
        };

        const priceLayout = {
            title: `${this.currentSymbol} 주가 차트`,
            xaxis: { title: '날짜' },
            yaxis: { title: '가격 ($)' },
            template: 'plotly_white'
        };

        Plotly.newPlot('priceChart', [priceTrace], priceLayout);

        const volumeTrace = {
            x: dates,
            y: volumes,
            type: 'bar',
            name: 'Volume',
            marker: { color: 'lightblue' }
        };

        const volumeLayout = {
            title: `${this.currentSymbol} 거래량`,
            xaxis: { title: '날짜' },
            yaxis: { title: '거래량' },
            template: 'plotly_white'
        };

        Plotly.newPlot('volumeChart', [volumeTrace], volumeLayout);

        this.createIndicatorsChart(data);
    }

    createIndicatorsChart(data) {
        if (data.length < 20) return;

        const dates = data.map(d => d.date);
        const prices = data.map(d => d.close);

        const sma20 = this.calculateSMA(prices, 20);

        const bb = this.calculateBollingerBands(prices, 20, 2);

        const traces = [
            {
                x: dates,
                y: prices,
                type: 'scatter',
                mode: 'lines',
                name: 'Close Price',
                line: { color: '#1f77b4', width: 2 }
            },
            {
                x: dates,
                y: sma20,
                type: 'scatter',
                mode: 'lines',
                name: 'SMA 20',
                line: { color: 'orange', width: 1, dash: 'dash' }
            },
            {
                x: dates,
                y: bb.upper,
                type: 'scatter',
                mode: 'lines',
                name: 'BB Upper',
                line: { color: 'red', width: 1, dash: 'dot' },
                fill: 'tonexty',
                fillcolor: 'rgba(255,0,0,0.1)'
            },
            {
                x: dates,
                y: bb.lower,
                type: 'scatter',
                mode: 'lines',
                name: 'BB Lower',
                line: { color: 'red', width: 1, dash: 'dot' }
            }
        ];

        const layout = {
            title: `${this.currentSymbol} 기술적 지표`,
            xaxis: { title: '날짜' },
            yaxis: { title: '가격 ($)' },
            template: 'plotly_white'
        };

        Plotly.newPlot('indicatorsChart', traces, layout);
    }

    calculateSMA(prices, period) {
        const sma = [];
        for (let i = 0; i < prices.length; i++) {
            if (i < period - 1) {
                sma.push(null);
            } else {
                const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
                sma.push(sum / period);
            }
        }
        return sma;
    }

    calculateBollingerBands(prices, period, stdDev) {
        const sma = this.calculateSMA(prices, period);
        const upper = [];
        const lower = [];

        for (let i = 0; i < prices.length; i++) {
            if (i < period - 1) {
                upper.push(null);
                lower.push(null);
            } else {
                const slice = prices.slice(i - period + 1, i + 1);
                const mean = sma[i];
                const variance = slice.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / period;
                const std = Math.sqrt(variance);

                upper.push(mean + (std * stdDev));
                lower.push(mean - (std * stdDev));
            }
        }

        return { upper, lower };
    }

    updateAnalysisDetails(analysisData) {
        const indicators = analysisData.signals || {};
        const indicatorsHtml = `
      <div>• RSI (14): ${(indicators.rsi || 0).toFixed(2)}</div>
      <div>• MACD: ${(indicators.macd || 0).toFixed(4)}</div>
      <div>• MACD Signal: ${(indicators.macd_signal || 0).toFixed(4)}</div>
      <div>• 볼린저 밴드 상단: $${(indicators.bb_upper || 0).toFixed(2)}</div>
      <div>• 볼린저 밴드 하단: $${(indicators.bb_lower || 0).toFixed(2)}</div>
    `;
        document.getElementById('technicalIndicators').innerHTML = indicatorsHtml;

        const statsHtml = `
      <div>• 평균 가격: $${(Math.random() * 100 + 100).toFixed(2)}</div>
      <div>• 최고가: $${(Math.random() * 50 + 150).toFixed(2)}</div>
      <div>• 최저가: $${(Math.random() * 50 + 80).toFixed(2)}</div>
      <div>• 평균 거래량: ${(Math.random() * 2000000 + 1000000).toLocaleString()}</div>
      <div>• 최대 거래량: ${(Math.random() * 5000000 + 2000000).toLocaleString()}</div>
    `;
        document.getElementById('tradingStats').innerHTML = statsHtml;
    }

    updateDataTable(historicalData) {
        if (!historicalData.data || historicalData.data.length === 0) return;

        const tbody = document.querySelector('#dataTable tbody');
        const recentData = historicalData.data.slice(-10).reverse();

        tbody.innerHTML = recentData.map(row => `
      <tr>
        <td>${new Date(row.date).toLocaleDateString()}</td>
        <td>$${row.close.toFixed(2)}</td>
        <td>${row.volume.toLocaleString()}</td>
        <td>${(row.rsi || 0).toFixed(2)}</td>
        <td>${(row.macd || 0).toFixed(4)}</td>
        <td>${(row.bb_upper || 0).toFixed(2)}</td>
        <td>${(row.bb_lower || 0).toFixed(2)}</td>
      </tr>
    `).join('');
    }

    updateRealtimeData(data) {
        if (Array.isArray(data)) {
            const currentStock = data.find(stock => stock.symbol === this.currentSymbol);
            if (currentStock) {
                this.updateMetrics(currentStock, currentStock);
            }
        }
    }

    showLoading() {
        const loadingElements = document.querySelectorAll('.loading');
        loadingElements.forEach(el => {
            el.style.display = 'block';
        });
    }

    showError(message) {
        const containers = ['technicalIndicators', 'tradingStats'];
        containers.forEach(id => {
            const container = document.getElementById(id);
            container.innerHTML = `<div style="color: #e74c3c;">${message}</div>`;
        });
    }

    startAutoRefresh() {
        this.autoRefreshInterval = setInterval(() => {
            this.loadData();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    new StockDashboard();
});
