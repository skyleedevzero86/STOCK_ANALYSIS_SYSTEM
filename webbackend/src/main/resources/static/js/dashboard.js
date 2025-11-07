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
        const symbolSelectBtn = document.getElementById('symbolSelectBtn');
        if (symbolSelectBtn) {
            symbolSelectBtn.addEventListener('click', () => {
                this.toggleSymbolSelectCard();
            });
        }

        const modalCloseBtn = document.getElementById('modalCloseBtn');
        if (modalCloseBtn) {
            modalCloseBtn.addEventListener('click', () => {
                const modal = document.getElementById('symbolSelectModal');
                if (modal) {
                    this.closeModal(modal);
                }
            });
        }

        const modal = document.getElementById('symbolSelectModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal);
                }
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.getElementById('symbolSelectModal');
                if (modal && modal.style.display !== 'none') {
                    this.closeModal(modal);
                }
            }
        });

        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.switchTab(button.dataset.tab, button);
            });
        });

        document.getElementById('symbolSelect').addEventListener('change', (e) => {
            this.currentSymbol = e.target.value;
            if (typeof window.updateCurrentSymbol === 'function') {
                window.updateCurrentSymbol(this.currentSymbol);
            }
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

    toggleSymbolSelectCard() {
        const modal = document.getElementById('symbolSelectModal');
        if (modal) {
            if (modal.style.display === 'none' || modal.style.display === '') {
                this.openModal(modal);
            } else {
                this.closeModal(modal);
            }
        }
    }

    openModal(modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        setTimeout(() => {
            modal.style.opacity = '1';
            const modalContent = modal.querySelector('.modal-content');
            if (modalContent) {
                modalContent.style.transform = 'scale(1)';
            }
        }, 10);
    }

    closeModal(modal) {
        modal.style.opacity = '0';
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.transform = 'scale(0.9)';
        }
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }, 300);
    }

    switchTab(tabName, buttonElement) {
        const tabbedCard = buttonElement.closest('.tabbed-card');
        if (!tabbedCard) return;
        
        const tabButtons = tabbedCard.querySelectorAll('.tab-button');
        const tabPanes = tabbedCard.querySelectorAll('.tab-pane');
        
        tabButtons.forEach(button => {
            button.classList.remove('active');
        });
        
        tabPanes.forEach(pane => {
            pane.classList.remove('active');
        });
        
        const activeButton = tabbedCard.querySelector(`[data-tab="${tabName}"]`);
        const activePane = tabbedCard.querySelector(`#${tabName}Tab`);
        
        if (activeButton) {
            activeButton.classList.add('active');
        }
        
        if (activePane) {
            activePane.classList.add('active');
            
            setTimeout(() => {
                const priceChart = activePane.querySelector('#priceChart');
                const volumeChart = activePane.querySelector('#volumeChart');
                
                if (priceChart && priceChart.innerHTML.trim() === '') {
                    if (this.lastHistoricalData) {
                        this.updateCharts(this.lastHistoricalData);
                    }
                }
                
                if (volumeChart && volumeChart.innerHTML.trim() === '') {
                    if (this.lastHistoricalData) {
                        this.updateCharts(this.lastHistoricalData);
                    }
                }
            }, 50);
        }
    }

    async loadInitialData() {
        await this.loadData();
    }

    async loadData() {
        try {
            this.showLoading();

            let realtimeData = null;
            let historicalData = null;
            let analysisData = null;

            try {
                const realtimeResponse = await axios.get(
                    `${this.apiBaseUrl}/api/stocks/realtime/${this.currentSymbol}`,
                    { timeout: 10000 }
                );
                realtimeData = realtimeResponse.data;
            } catch (error) {
                console.warn("실시간 데이터 로드 실패, 더미 데이터 사용:", error);
                realtimeData = this.generateDummyRealtimeData();
            }

            try {
                const historicalResponse = await axios.get(
                    `${this.apiBaseUrl}/api/stocks/historical/${this.currentSymbol}?days=${this.currentDays}`,
                    { timeout: 15000 }
                );
                historicalData = historicalResponse.data;
            } catch (error) {
                console.warn("과거 데이터 로드 실패, 더미 데이터 사용:", error);
                historicalData = this.generateDummyHistoricalData();
            }

            try {
                const analysisResponse = await axios.get(
                    `${this.apiBaseUrl}/api/stocks/analysis/${this.currentSymbol}`,
                    { timeout: 15000 }
                );
                analysisData = analysisResponse.data;
            } catch (error) {
                console.warn("분석 데이터 로드 실패, 더미 데이터 사용:", error);
                analysisData = this.generateDummyAnalysisData();
            }

            this.updateMetrics(realtimeData, analysisData);
            this.updateCharts(historicalData);
            this.updateAnalysisDetails(analysisData);
            this.updateTradingStats(historicalData);
            this.updateDataTable(historicalData);
            this.hideLoading();

        } catch (error) {
            console.error("데이터 로드 실패:", error);
            this.hideLoading();
            this.showErrorWithInstructions(error);
        }
    }

    generateDummyRealtimeData() {
        const basePrice = 150 + Math.random() * 50;
        const changePercent = (Math.random() - 0.5) * 10;
        return {
            symbol: this.currentSymbol,
            currentPrice: basePrice,
            price: basePrice,
            volume: Math.floor(Math.random() * 5000000) + 1000000,
            changePercent: changePercent,
            change_percent: changePercent,
            timestamp: new Date().toISOString(),
            confidenceScore: 0.5
        };
    }

    generateDummyHistoricalData() {
        const days = this.currentDays;
        const data = [];
        const basePrice = 150;
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            const price = basePrice + Math.sin(i / 10) * 20 + Math.random() * 10;
            const volume = Math.floor(Math.random() * 3000000) + 500000;
            
            data.push({
                date: date.toISOString().split('T')[0],
                close: price,
                volume: volume,
                rsi: 50 + Math.random() * 20,
                macd: (Math.random() - 0.5) * 2,
                bb_upper: price + 10,
                bb_lower: price - 10,
                sma_20: price
            });
        }
        
        return { symbol: this.currentSymbol, data: data, period: days };
    }

    generateDummyAnalysisData() {
        return {
            symbol: this.currentSymbol,
            trend: Math.random() > 0.5 ? "bullish" : "bearish",
            trendStrength: Math.random() * 0.5 + 0.5,
            signals: {
                signal: Math.random() > 0.5 ? "buy" : "hold",
                confidence: Math.random() * 0.3 + 0.7,
                rsi: 50 + Math.random() * 20,
                macd: (Math.random() - 0.5) * 2,
                macdSignal: (Math.random() - 0.5) * 2,
                macd_signal: (Math.random() - 0.5) * 2
            },
            anomalies: []
        };
    }

    showErrorWithInstructions(error) {
        let errorMessage = "데이터를 불러올 수 없습니다.";

        if (error.response) {
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
                errorMessage = `데이터를 찾을 수 없습니다 (404).<br>종목 심볼 "${this.currentSymbol}"이 유효한지 확인하세요.<br><br>` +
                    `더미 데이터를 표시합니다.`;
            } else if (serverMessage) {
                errorMessage = `오류 발생 (${status}): ${serverMessage}<br><br>더미 데이터를 표시합니다.`;
            } else {
                errorMessage = `서버 오류 (${status}). 잠시 후 다시 시도하세요.<br><br>더미 데이터를 표시합니다.`;
            }
        } else if (error.request) {
            errorMessage = `서버에 연결할 수 없습니다.<br><br>` +
                `<strong>Spring Boot 백엔드 서버가 실행 중인지 확인하세요.</strong><br>` +
                `또는 Python API 서버가 실행 중인지 확인하세요:<br>` +
                `<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">python start_python_api.py</code><br><br>` +
                `더미 데이터를 표시합니다.`;
        } else {
                errorMessage = `요청 오류: ${error.message}<br><br>더미 데이터를 표시합니다.`;
        }

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notice';
        errorDiv.style.cssText = 'background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 12px; margin-bottom: 20px; color: #856404;';
        errorDiv.innerHTML = `<strong>주의:</strong> ${errorMessage}`;
        
        const firstCard = document.querySelector('.card');
        if (firstCard && !document.querySelector('.error-notice')) {
            firstCard.parentNode.insertBefore(errorDiv, firstCard);
        }

        const realtimeData = this.generateDummyRealtimeData();
        const historicalData = this.generateDummyHistoricalData();
        const analysisData = this.generateDummyAnalysisData();
        
        this.updateMetrics(realtimeData, analysisData);
        this.updateCharts(historicalData);
        this.updateAnalysisDetails(analysisData);
        this.updateTradingStats(historicalData);
        this.updateDataTable(historicalData);
    }

    hideLoading() {
        const loadingElements = document.querySelectorAll('.loading');
        loadingElements.forEach(el => {
            el.style.display = 'none';
        });
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

        const rsiEl = document.getElementById('rsi');
        const rsiStatusEl = document.getElementById('rsiStatus');

        if (hasRsiData) {
            rsiEl.textContent = rsi.toFixed(1);
            rsiEl.className = "indicator-value";
            const rsiStatus = rsi > 70 ? "과매수" : rsi < 30 ? "과매도" : "정상";
            rsiStatusEl.textContent = rsiStatus;
            if (rsiStatus === "정상") {
                rsiStatusEl.className = "indicator-status status-normal";
            } else {
                rsiStatusEl.className = "indicator-status";
            }
        } else {
            rsiEl.textContent = "N/A";
            rsiEl.className = "indicator-value";
            rsiStatusEl.textContent = "데이터 없음";
            rsiStatusEl.className = "indicator-status";
        }

        const macdValue = analysisData.signals?.macd;
        const macdSignalValue = analysisData.signals?.macdSignal !== undefined
            ? analysisData.signals.macdSignal
            : analysisData.signals?.macd_signal;
        const hasMacdData = macdValue !== null && macdValue !== undefined && macdValue !== 0;

        const macd = safeValue(macdValue, 0);
        const macdSignal = safeValue(macdSignalValue, 0);

        const macdEl = document.getElementById('macd');
        const macdStatusEl = document.getElementById('macdStatus');

        if (hasMacdData) {
            macdEl.textContent = macd.toFixed(3);
            if (macd < 0) {
                macdEl.className = "indicator-value macd-negative";
            } else {
                macdEl.className = "indicator-value";
            }
            const macdStatus = macd > macdSignal ? "상승" : "하락";
            macdStatusEl.textContent = macdStatus;
            if (macdStatus === "상승") {
                macdStatusEl.className = "indicator-status status-up";
            } else {
                macdStatusEl.className = "indicator-status status-down status-down-red";
            }
        } else {
            macdEl.textContent = "N/A";
            macdEl.className = "indicator-value";
            macdStatusEl.textContent = "데이터 없음";
            macdStatusEl.className = "indicator-status";
        }
    }

    updateCharts(historicalData) {
        if (!historicalData || !historicalData.data || historicalData.data.length === 0) {
            console.warn("차트 데이터가 없습니다. 더미 데이터를 생성합니다.");
            historicalData = this.generateDummyHistoricalData();
        }

        this.lastHistoricalData = historicalData;

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

        const priceChartEl = document.getElementById('priceChart');
        if (priceChartEl) {
            Plotly.newPlot('priceChart', [priceTrace], priceLayout);
        } else {
            console.warn("priceChart 요소가 페이지에 없습니다.");
        }

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

        const volumeChartEl = document.getElementById('volumeChart');
        if (volumeChartEl) {
            Plotly.newPlot('volumeChart', [volumeTrace], volumeLayout);
        } else {
            console.warn("volumeChart 요소가 페이지에 없습니다.");
        }

        this.createIndicatorsChart(data);
    }

    createIndicatorsChart(data) {
        const indicatorsChartEl = document.getElementById('indicatorsChart');
        if (!indicatorsChartEl) {
            console.warn("indicatorsChart 요소가 페이지에 없습니다. 차트를 생성하지 않습니다.");
            return;
        }

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
        const technicalIndicatorsEl = document.getElementById('technicalIndicators');
        if (technicalIndicatorsEl) {
            technicalIndicatorsEl.innerHTML = indicatorsHtml;
        }
    }

    updateTradingStats(historicalData) {
        if (!historicalData || !historicalData.data || historicalData.data.length === 0) {
            console.warn("거래 통계 데이터가 없습니다. 더미 데이터를 생성합니다.");
            historicalData = this.generateDummyHistoricalData();
        }

        const safeValue = (value, defaultValue = 0) => {
            return (value !== null && value !== undefined && !isNaN(value)) ? Number(value) : defaultValue;
        };

        const data = historicalData.data;
        const prices = data.map(d => safeValue(d.close, 0)).filter(p => p > 0);
        const volumes = data.map(d => safeValue(d.volume, 0)).filter(v => v > 0);

        if (prices.length === 0 || volumes.length === 0) {
            const tradingStatsEl = document.getElementById('tradingStats');
            if (tradingStatsEl) {
                tradingStatsEl.innerHTML = '<div style="color: #666; padding: 20px; text-align: center;">데이터를 불러오는 중...</div>';
            }
            return;
        }

        const avgPrice = prices.reduce((sum, price) => sum + price, 0) / prices.length;
        const maxPrice = Math.max(...prices);
        const minPrice = Math.min(...prices);
        const avgVolume = volumes.reduce((sum, vol) => sum + vol, 0) / volumes.length;
        const maxVolume = Math.max(...volumes);

        const statsHtml = `
      <div>• 평균 가격: $${avgPrice.toFixed(2)}</div>
      <div>• 최고가: $${maxPrice.toFixed(2)}</div>
      <div>• 최저가: $${minPrice.toFixed(2)}</div>
      <div>• 평균 거래량: ${avgVolume.toLocaleString('ko-KR', { maximumFractionDigits: 3 })}</div>
      <div>• 최대 거래량: ${maxVolume.toLocaleString('ko-KR', { maximumFractionDigits: 3 })}</div>
    `;
        const tradingStatsEl = document.getElementById('tradingStats');
        if (tradingStatsEl) {
            tradingStatsEl.innerHTML = statsHtml;
        }
    }

    updateDataTable(historicalData) {
        if (!historicalData || !historicalData.data || historicalData.data.length === 0) {
            console.warn("테이블 데이터가 없습니다. 더미 데이터를 생성합니다.");
            historicalData = this.generateDummyHistoricalData();
        }

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

            const getValueClass = (value) => value < 0 ? 'negative-value' : '';
            const getValueStyle = (value) => value < 0 ? 'style="color: #e74c3c; font-weight: 600;"' : '';

            return `
      <tr>
        <td>${date}</td>
        <td>$${close.toFixed(2)}</td>
        <td>${volume.toLocaleString()}</td>
        <td ${getValueStyle(rsi)}>${rsi.toFixed(2)}</td>
        <td ${getValueStyle(macd)}>${macd.toFixed(4)}</td>
        <td ${getValueStyle(bbUpper)}>${bbUpper.toFixed(2)}</td>
        <td ${getValueStyle(bbLower)}>${bbLower.toFixed(2)}</td>
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
    window.dashboard = dashboard;
});