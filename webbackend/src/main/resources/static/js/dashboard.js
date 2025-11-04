class StockDashboard {
    constructor() {
        this.apiBaseUrl = "http://localhost:8080";
        this.pythonApiUrl = "http://localhost:9000";
        this.wsUrl = "ws://localhost:8080/ws/stocks";
        this.charts = {};
        this.currentSymbol = "AAPL";
        this.currentDays = 30;
        this.autoRefreshInterval = null;
        this.healthCheckInterval = null;
        this.ws = null;
        this.wsReconnectAttempts = 0;
        this.wsMessageCount = 0;
        this.lastUpdateTime = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setupWebSocket();
        this.startHealthCheck();
        this.updateConnectionStatus();
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
            let errorMessage = "데이터를 불러올 수 없습니다.";

            if (error.response) {
                console.error("서버 응답 상태:", error.response.status);
                console.error("서버 응답 데이터:", error.response.data);

                const status = error.response.status;
                const serverMessage = error.response.data?.message || error.response.data?.error || "";

                if (status === 503) {
                    errorMessage = `서비스 일시 중단 (503)<br>` +
                        `<strong>Python API 서버가 실행되지 않은 것 같습니다.</strong><br><br>` +
                        `다음 명령으로 서버를 시작하세요:<br>` +
                        `<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">python start_python_api.py</code><br><br>` +
                        `또는:<br>` +
                        `<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">uvicorn api_server:app --port 9000</code><br><br>` +
                        `서버 시작 후 페이지를 새로고침하세요.`;
                } else if (status === 404) {
                    errorMessage = `데이터를 찾을 수 없습니다 (404).<br>종목 심볼 "${this.currentSymbol}"이 유효한지 확인하세요.`;
                } else if (serverMessage) {
                    errorMessage = `오류 발생 (${status}): ${serverMessage}`;
                    if (serverMessage.includes("Python API")) {
                        errorMessage += `<br><br>Python API 서버를 시작하세요: <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">python start_python_api.py</code>`;
                    }
                } else {
                    errorMessage = `서버 오류 (${status}). 잠시 후 다시 시도하세요.`;
                }
            } else if (error.request) {
                console.error("서버 응답 없음:", error.request);
                errorMessage = `서버에 연결할 수 없습니다.<br><br>` +
                    `<strong>Spring Boot 백엔드 서버가 실행 중인지 확인하세요.</strong><br>` +
                    `또는 Python API 서버가 실행 중인지 확인하세요:<br>` +
                    `<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">python start_python_api.py</code>`;
            } else {
                console.error("요청 설정 오류:", error.message);
                errorMessage = `요청 오류: ${error.message}`;
            }

            this.showError(errorMessage);
        }
    }

    setupWebSocket() {
        try {
            this.updateWebSocketStatus("연결 중...", "neutral");
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                console.log("WebSocket 연결됨");
                this.wsReconnectAttempts = 0;
                this.updateWebSocketStatus("연결됨", "positive");
                this.updateConnectionStatus();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.wsMessageCount++;
                    this.lastUpdateTime = new Date();
                    this.updateRealtimeData(data);
                    this.updateConnectionStatus();
                } catch (error) {
                    console.error("WebSocket 메시지 파싱 오류:", error);
                }
            };

            this.ws.onclose = () => {
                console.log("WebSocket 연결 끊어짐");
                this.wsReconnectAttempts++;
                this.updateWebSocketStatus(`연결 끊김 (재연결 시도: ${this.wsReconnectAttempts})`, "negative");
                this.updateConnectionStatus();

                if (this.wsReconnectAttempts < 10) {
                    setTimeout(() => this.setupWebSocket(), 5000);
                } else {
                    this.updateWebSocketStatus("연결 실패 (최대 시도 횟수 초과)", "negative");
                }
            };

            this.ws.onerror = (error) => {
                console.error("WebSocket 오류:", error);
                this.updateWebSocketStatus("연결 오류", "negative");
                this.updateConnectionStatus();
            };
        } catch (error) {
            console.error("WebSocket 설정 실패:", error);
            this.updateWebSocketStatus("설정 실패", "negative");
            this.updateConnectionStatus();
        }
    }

    updateWebSocketStatus(status, className) {
        const wsStatusEl = document.getElementById('wsStatus');
        if (wsStatusEl) {
            wsStatusEl.textContent = status;
            wsStatusEl.className = `status-value ${className}`;
        }
    }

    updateConnectionStatus() {
        const lastUpdateEl = document.getElementById('lastUpdateTime');
        if (lastUpdateEl) {
            if (this.lastUpdateTime) {
                const timeString = this.lastUpdateTime.toLocaleTimeString();
                lastUpdateEl.textContent = timeString;
                lastUpdateEl.className = "status-value neutral";
            } else {
                lastUpdateEl.textContent = "-";
                lastUpdateEl.className = "status-value neutral";
            }
        }

        const messageCountEl = document.getElementById('messageCount');
        if (messageCountEl) {
            messageCountEl.textContent = this.wsMessageCount.toString();
            messageCountEl.className = "status-value neutral";
        }

        const reconnectCountEl = document.getElementById('reconnectCount');
        if (reconnectCountEl) {
            reconnectCountEl.textContent = this.wsReconnectAttempts.toString();
            reconnectCountEl.className = this.wsReconnectAttempts > 0
                ? "status-value warning"
                : "status-value neutral";
        }
    }

    async checkSystemHealth() {
        const checkButton = document.querySelector('button[onclick="dashboard.checkSystemHealth()"]');
        if (checkButton) {
            checkButton.textContent = "체크 중...";
            checkButton.disabled = true;
            checkButton.style.backgroundColor = "#f39c12";
        }

        try {
            try {
                const response = await axios.get(`${this.apiBaseUrl}/api/stocks/symbols`, {
                    timeout: 5000,
                    validateStatus: function (status) {
                        return status >= 200 && status < 500;
                    }
                });
                if (response.status === 200) {
                    this.updateApiStatus("정상", "positive");
                } else {
                    this.updateApiStatus("응답 오류", "warning");
                }
            } catch (error) {
                if (error.code === 'ECONNREFUSED' || error.code === 'ERR_CONNECTION_REFUSED') {
                    this.updateApiStatus("연결 실패", "negative");
                } else if (error.message.includes('timeout')) {
                    this.updateApiStatus("타임아웃", "warning");
                } else {
                    this.updateApiStatus("연결 실패", "negative");
                }
            }

            try {
                const response = await axios.get(`${this.pythonApiUrl}/api/health`, {
                    timeout: 5000,
                    validateStatus: function (status) {
                        return status >= 200 && status < 500;
                    }
                });

                if (response.status === 200) {
                    this.updatePythonApiStatus("정상", "positive");
                } else {
                    this.updatePythonApiStatus("응답 오류", "warning");
                }
            } catch (error) {
                const errorCode = error.code || error.response?.status;
                const errorMessage = error.message || '';
                const isConnectionRefused =
                    errorCode === 'ECONNREFUSED' ||
                    errorCode === 'ERR_CONNECTION_REFUSED' ||
                    errorMessage.includes('ERR_CONNECTION_REFUSED') ||
                    errorMessage.includes('Network Error') ||
                    errorMessage.includes('Failed to fetch');

                const isTimeout =
                    errorCode === 'ECONNABORTED' ||
                    errorMessage.includes('timeout') ||
                    errorMessage.includes('Timeout');

                if (isConnectionRefused) {
                    this.updatePythonApiStatus("서버 미실행", "warning");
                } else if (isTimeout) {
                    this.updatePythonApiStatus("타임아웃", "warning");
                } else {
                    this.updatePythonApiStatus("연결 실패", "warning");
                }
            }

            if (checkButton) {
                checkButton.textContent = "체크 완료";
                checkButton.style.backgroundColor = "#27ae60";
                setTimeout(() => {
                    checkButton.textContent = "시스템 체크";
                    checkButton.style.backgroundColor = "#3498db";
                    checkButton.disabled = false;
                }, 2000);
            }
        } catch (error) {
            if (checkButton) {
                checkButton.textContent = "체크 실패";
                checkButton.style.backgroundColor = "#e74c3c";
                setTimeout(() => {
                    checkButton.textContent = "시스템 체크";
                    checkButton.style.backgroundColor = "#3498db";
                    checkButton.disabled = false;
                }, 2000);
            }
        }
    }

    updateApiStatus(status, className) {
        const apiStatusEl = document.getElementById('apiStatus');
        if (apiStatusEl) {
            apiStatusEl.textContent = status;
            apiStatusEl.className = `status-value ${className}`;
        }
    }

    updatePythonApiStatus(status, className) {
        const pythonApiStatusEl = document.getElementById('pythonApiStatus');
        if (pythonApiStatusEl) {
            pythonApiStatusEl.textContent = status;
            pythonApiStatusEl.className = `status-value ${className}`;
        }
    }

    startHealthCheck() {
        setTimeout(() => {
            this.checkSystemHealth();
        }, 1000);

        this.healthCheckInterval = setInterval(() => {
            this.checkSystemHealth();
        }, 30000);
    }

    resetConnectionStats() {
        const resetButton = document.querySelector('button[onclick="dashboard.resetConnectionStats()"]');
        if (resetButton) {
            resetButton.textContent = "리셋 중...";
            resetButton.disabled = true;
            resetButton.style.backgroundColor = "#f39c12";
        }

        const statusValues = document.querySelectorAll("#connectionStatus .status-value");
        statusValues.forEach((value) => {
            value.style.transition = "all 0.3s ease";
            value.style.transform = "scale(0.9)";
            value.style.opacity = "0.5";
        });

        setTimeout(() => {
            this.wsMessageCount = 0;
            this.wsReconnectAttempts = 0;
            this.lastUpdateTime = null;
            this.updateConnectionStatus();

            statusValues.forEach((value) => {
                value.style.transform = "scale(1.1)";
                value.style.opacity = "1";
                setTimeout(() => {
                    value.style.transform = "scale(1)";
                }, 200);
            });

            if (resetButton) {
                resetButton.textContent = "리셋 완료";
                resetButton.style.backgroundColor = "#27ae60";
                setTimeout(() => {
                    resetButton.textContent = "통계 리셋";
                    resetButton.style.backgroundColor = "#3498db";
                    resetButton.disabled = false;
                }, 2000);
            }
        }, 500);
    }

    updateMetrics(realtimeData, analysisData) {
        const safeValue = (value, defaultValue = 0) => {
            return (value !== null && value !== undefined && !isNaN(value)) ? Number(value) : defaultValue;
        };

        const price = safeValue(
            realtimeData.currentPrice !== undefined ? realtimeData.currentPrice : realtimeData.price,
            0
        );
        const changePercent = safeValue(
            realtimeData.changePercent !== undefined ? realtimeData.changePercent : realtimeData.change_percent,
            0
        );

        document.getElementById('currentPrice').textContent = `$${price.toFixed(2)}`;
        document.getElementById('priceChange').textContent =
            `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
        document.getElementById('priceChange').className =
            `metric-change ${changePercent >= 0 ? 'positive' : 'negative'}`;

        const volume = safeValue(realtimeData.volume, 0);
        document.getElementById('volume').textContent = volume.toLocaleString();

        const volumeChange = safeValue(
            realtimeData.volumeChange !== undefined
                ? realtimeData.volumeChange
                : realtimeData.volume_change,
            Math.floor(Math.random() * 100000)
        );
        const volumeChangeAbs = Math.abs(volumeChange);
        const volumeChangeSign = volumeChange >= 0 ? '+' : '-';
        document.getElementById('volumeChange').textContent = `${volumeChangeSign}${volumeChangeAbs.toLocaleString()}`;

        const rsiValue = analysisData.signals?.rsi;
        const hasRsiData = rsiValue !== null && rsiValue !== undefined && rsiValue !== 0;
        const rsi = safeValue(rsiValue, 0);

        if (hasRsiData) {
            document.getElementById('rsi').textContent = rsi.toFixed(1);
            const rsiStatus = rsi > 70 ? "과매수" : rsi < 30 ? "과매도" : "정상";
            document.getElementById('rsiStatus').textContent = rsiStatus;
        } else {
            document.getElementById('rsi').textContent = "N/A";
            document.getElementById('rsiStatus').textContent = "데이터 없음";
            document.getElementById('rsiStatus').className = "indicator-status";
        }

        const macdValue = analysisData.signals?.macd;
        const macdSignalValue = analysisData.signals?.macdSignal !== undefined
            ? analysisData.signals.macdSignal
            : analysisData.signals?.macd_signal;
        const hasMacdData = macdValue !== null && macdValue !== undefined && macdValue !== 0;

        const macd = safeValue(macdValue, 0);
        const macdSignal = safeValue(macdSignalValue, 0);

        if (hasMacdData) {
            document.getElementById('macd').textContent = macd.toFixed(3);
            const macdStatus = macd > macdSignal ? "상승" : "하락";
            document.getElementById('macdStatus').textContent = macdStatus;
        } else {
            document.getElementById('macd').textContent = "N/A";
            document.getElementById('macdStatus').textContent = "데이터 없음";
            document.getElementById('macdStatus').className = "indicator-status";
        }
    }

    updateCharts(historicalData) {
        if (!historicalData.data || historicalData.data.length === 0) return;

        const safeValue = (value, defaultValue = 0) => {
            return (value !== null && value !== undefined && !isNaN(value)) ? Number(value) : defaultValue;
        };

        const data = historicalData.data;
        const dates = data.map(d => d.date || '');
        const prices = data.map(d => safeValue(d.close, 0));
        const volumes = data.map(d => safeValue(d.volume, 0));

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

        const safeValue = (value, defaultValue = 0) => {
            return (value !== null && value !== undefined && !isNaN(value)) ? Number(value) : defaultValue;
        };

        const dates = data.map(d => d.date || '');
        const prices = data.map(d => safeValue(d.close, 0));

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
        const safeValue = (value, defaultValue = 0) => {
            return (value !== null && value !== undefined && !isNaN(value)) ? Number(value) : defaultValue;
        };

        const indicators = analysisData.signals || {};
        const rsi = safeValue(indicators.rsi, 0);
        const macd = safeValue(indicators.macd, 0);
        const macdSignal = safeValue(
            indicators.macdSignal !== undefined ? indicators.macdSignal : indicators.macd_signal,
            0
        );
        const bbUpper = safeValue(indicators.bb_upper, 0);
        const bbLower = safeValue(indicators.bb_lower, 0);

        const indicatorsHtml = `
      <div>• RSI (14): ${rsi.toFixed(2)}</div>
      <div>• MACD: ${macd.toFixed(4)}</div>
      <div>• MACD Signal: ${macdSignal.toFixed(4)}</div>
      <div>• 볼린저 밴드 상단: $${bbUpper.toFixed(2)}</div>
      <div>• 볼린저 밴드 하단: $${bbLower.toFixed(2)}</div>
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

        const safeValue = (value, defaultValue = 0) => {
            return (value !== null && value !== undefined && !isNaN(value)) ? Number(value) : defaultValue;
        };

        const tbody = document.querySelector('#dataTable tbody');
        const recentData = historicalData.data.slice(-10).reverse();

        tbody.innerHTML = recentData.map(row => {
            const close = safeValue(row.close, 0);
            const volume = safeValue(row.volume, 0);
            const rsi = safeValue(row.rsi, 0);
            const macd = safeValue(row.macd, 0);
            const bbUpper = safeValue(row.bb_upper, 0);
            const bbLower = safeValue(row.bb_lower, 0);
            const date = row.date ? new Date(row.date).toLocaleDateString() : 'N/A';

            return `
      <tr>
        <td>${date}</td>
        <td>$${close.toFixed(2)}</td>
        <td>${volume.toLocaleString()}</td>
        <td>${rsi.toFixed(2)}</td>
        <td>${macd.toFixed(4)}</td>
        <td>${bbUpper.toFixed(2)}</td>
        <td>${bbLower.toFixed(2)}</td>
      </tr>
    `;
        }).join('');
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
        const containers = ['technicalIndicators', 'tradingStats', 'chartContainer', 'dataTableContainer'];
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `<div style="color: #e74c3c; padding: 20px; background: #fee; border: 1px solid #fcc; border-radius: 8px; margin: 20px 0;">
                    <strong>오류 발생</strong><br><br>
                    ${message}
                </div>`;
            }
        });

        const metricsGrid = document.querySelector('.metrics-grid');
        if (metricsGrid) {
            metricsGrid.innerHTML = `<div style="grid-column: 1 / -1; color: #e74c3c; padding: 20px; background: #fee; border: 1px solid #fcc; border-radius: 8px;">
                <strong>오류 발생</strong><br><br>
                ${message}
            </div>`;
        }

        const chartSection = document.querySelector('.charts-section');
        if (chartSection) {
            const existingError = chartSection.querySelector('.error-message');
            if (!existingError) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.style.cssText = 'color: #e74c3c; padding: 20px; background: #fee; border: 1px solid #fcc; border-radius: 8px; margin: 20px 0;';
                errorDiv.innerHTML = `<strong>오류 발생</strong><br><br>${message}`;
                chartSection.insertBefore(errorDiv, chartSection.firstChild);
            }
        }
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

let dashboard;

document.addEventListener("DOMContentLoaded", () => {
    dashboard = new StockDashboard();
});