window.addEventListener('unhandledrejection', function(event) {
    const error = event.reason;
    const errorMessage = error?.message || '';
    const errorStack = error?.stack || '';
    const errorString = String(error);
    const errorName = error?.name || '';
    
    if (errorMessage.includes('ERR_CONNECTION_REFUSED') || 
        errorMessage.includes('Failed to fetch') ||
        errorMessage.includes('NetworkError') ||
        errorMessage.includes('Connection refused') ||
        errorStack.includes('/api/health') ||
        errorStack.includes('checkSystemHealth') ||
        errorString.includes('ERR_CONNECTION_REFUSED') ||
        errorString.includes('/api/health') ||
        errorName === 'TypeError' ||
        errorName === 'NetworkError') {
        event.preventDefault();
        return;
    }
});

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
        this.lastResponseTime = null;
        this.sectorSliderCurrentIndex = 0;
        this.sectorSliderHandlers = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setupWebSocket();
        this.startHealthCheck();
        this.updateConnectionStatus();
        this.loadTopPerformers();
        this.loadSectorsAnalysis();
        setInterval(() => this.loadTopPerformers(), 60000);
        setInterval(() => this.loadSectorsAnalysis(), 120000);
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

        const responseTimeEl = document.getElementById('responseTime');
        if (responseTimeEl) {
            if (this.lastResponseTime !== null) {
                responseTimeEl.textContent = `${this.lastResponseTime}ms`;
                responseTimeEl.className = this.lastResponseTime < 500
                    ? "status-value positive"
                    : this.lastResponseTime < 1000
                    ? "status-value neutral"
                    : "status-value warning";
            } else {
                responseTimeEl.textContent = "-";
                responseTimeEl.className = "status-value neutral";
            }
        }
    }

    async checkSystemHealth() {
        const checkButton = document.querySelector('button[onclick="dashboard.checkSystemHealth()"]');
        if (checkButton) {
            checkButton.textContent = "체크 중...";
            checkButton.disabled = true;
            checkButton.style.backgroundColor = "#f39c12";
        }

        let kotlinApiSuccess = false;
        let pythonApiSuccess = false;

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
                    kotlinApiSuccess = true;
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
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);
                
                let response = null;
                let fetchError = null;
                try {
                    response = await fetch(`${this.pythonApiUrl}/api/health`, {
                        method: 'GET',
                        signal: controller.signal,
                        cache: 'no-cache',
                        mode: 'cors'
                    }).catch(() => null);
                } catch (error) {
                    clearTimeout(timeoutId);
                    fetchError = error;
                    response = null;
                }
                
                clearTimeout(timeoutId);
                
                if (response && response.ok) {
                    this.updatePythonApiStatus("정상", "positive");
                    pythonApiSuccess = true;
                } else if (response) {
                    this.updatePythonApiStatus("응답 오류", "warning");
                    pythonApiSuccess = false;
                } else {
                    this.updatePythonApiStatus("서버 미실행", "warning");
                    pythonApiSuccess = false;
                }
            } catch (error) {
                const errorMessage = error.message || '';
                const isConnectionRefused = 
                    errorMessage.includes('ERR_CONNECTION_REFUSED') ||
                    errorMessage.includes('Failed to fetch') ||
                    errorMessage.includes('NetworkError');
                const isTimeout =
                    errorMessage.includes('timeout') ||
                    errorMessage.includes('Timeout') ||
                    errorMessage.includes('aborted');

                if (isTimeout) {
                    this.updatePythonApiStatus("타임아웃", "warning");
                } else if (isConnectionRefused) {
                    this.updatePythonApiStatus("서버 미실행", "warning");
                } else {
                    this.updatePythonApiStatus("연결 실패", "warning");
                }
                pythonApiSuccess = false;
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
            
            return pythonApiSuccess;
        } catch {
            if (checkButton) {
                checkButton.textContent = "체크 실패";
                checkButton.style.backgroundColor = "#e74c3c";
                setTimeout(() => {
                    checkButton.textContent = "시스템 체크";
                    checkButton.style.backgroundColor = "#3498db";
                    checkButton.disabled = false;
                }, 2000);
            }
            return false;
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

    async loadTopPerformers(retryCount = 0) {
        const container = document.getElementById('topPerformersContainer');
        if (!container) return;

        const maxRetries = 2;
        const retryDelay = 3000;

        try {
            container.innerHTML = '<div class="loading">최고 성과 종목을 불러오는 중...</div>';
            
            const startTime = performance.now();
            const response = await axios.get(`${this.apiBaseUrl}/api/stocks/top-performers?limit=5`, {
                timeout: 65000,
                validateStatus: function (status) {
                    return status >= 200 && status < 500;
                }
            });
            const endTime = performance.now();
            this.lastResponseTime = Math.round(endTime - startTime);

            if (response.status === 200 && response.data && Array.isArray(response.data) && response.data.length > 0) {
                this.renderTopPerformers(response.data);
            } else if (response.status === 200 && (!response.data || !Array.isArray(response.data) || response.data.length === 0)) {
                if (retryCount < maxRetries) {
                    console.log(`최고 성과 종목 데이터가 비어있습니다. ${retryDelay/1000}초 후 재시도... (${retryCount + 1}/${maxRetries})`);
                    container.innerHTML = `<div class="loading">데이터를 기다리는 중... (${retryCount + 1}/${maxRetries} 재시도)</div>`;
                    setTimeout(() => {
                        this.loadTopPerformers(retryCount + 1);
                    }, retryDelay);
                } else {
                    container.innerHTML = `
                        <div class="no-data">
                            <p style="margin-bottom: 8px;">최고 성과 종목 데이터가 없습니다. 잠시 후</p>
                            <p style="margin-bottom: 16px;">다시 시도해주세요.</p>
                        </div>
                    `;
                }
            } else {
                const errorMsg = response.data?.message || response.data?.error || `서버 오류 (${response.status})`;
                container.innerHTML = `<div class="error">최고 성과 종목을 불러올 수 없습니다: ${errorMsg}</div>`;
                console.error('최고 성과 종목 로드 실패:', response.status, response.data);
            }
            this.updateConnectionStatus();
        } catch (error) {
            if (retryCount < maxRetries && (error.code === 'ECONNABORTED' || error.message?.includes('timeout'))) {
                console.log(`최고 성과 종목 로드 타임아웃. ${retryDelay/1000}초 후 재시도... (${retryCount + 1}/${maxRetries})`);
                container.innerHTML = `<div class="loading">연결 중... (${retryCount + 1}/${maxRetries} 재시도)</div>`;
                setTimeout(() => {
                    this.loadTopPerformers(retryCount + 1);
                }, retryDelay);
                return;
            }

            let errorMessage = '최고 성과 종목을 불러올 수 없습니다.';
            if (error.response) {
                errorMessage = `서버 오류: ${error.response.status} - ${error.response.data?.message || error.response.data?.error || '알 수 없는 오류'}`;
            } else if (error.request) {
                errorMessage = '서버에 연결할 수 없습니다. Python API 서버가 실행 중인지 확인하세요.';
            } else {
                errorMessage = `요청 오류: ${error.message}`;
            }
            container.innerHTML = `
                <div class="error">
                    <p>${errorMessage}</p>
                </div>
            `;
            console.error('최고 성과 종목 로드 중 예외 발생:', error);
        }
    }

    renderTopPerformers(performers) {
        const container = document.getElementById('topPerformersContainer');
        if (!container) return;

        const html = performers.map((stock, index) => {
            const changePercent = stock.changePercent || 0;
            const changeClass = changePercent >= 0 ? 'positive' : 'negative';
            const changeText = changePercent >= 0 ? `+${changePercent.toFixed(2)}%` : `${changePercent.toFixed(2)}%`;
            const score = stock.score || 0;
            const signal = stock.signal || 'hold';
            const signalClass = signal.toLowerCase().includes('buy') ? 'buy' : signal.toLowerCase().includes('sell') ? 'sell' : 'hold';

            return `
                <div class="top-performer-item">
                    <div class="performer-rank">${index + 1}</div>
                    <div class="performer-info">
                        <div class="performer-header">
                            <span class="performer-symbol">${stock.symbol}</span>
                            <span class="performer-price">$${stock.currentPrice?.toFixed(2) || '0.00'}</span>
                        </div>
                        <div class="performer-details">
                            <span class="performer-change ${changeClass}">${changeText}</span>
                            <span class="performer-signal signal-${signalClass}">${signal}</span>
                            <span class="performer-score">점수: ${score.toFixed(1)}</span>
                        </div>
                        <div class="performer-metrics">
                            <span class="performer-metric">RSI: ${stock.rsi?.toFixed(1) || '-'}</span>
                            <span class="performer-metric">신뢰도: ${(stock.confidence * 100)?.toFixed(0) || 0}%</span>
                            <span class="performer-metric">트렌드: ${stock.trendStrength?.toFixed(2) || 0}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = html;
    }

    async loadSectorsAnalysis() {
        const comparisonEl = document.getElementById('sectorStocksComparison');
        const bubbleChartEl = document.getElementById('sectorBubbleChart');
        
        try {
            const response = await axios.get(`${this.apiBaseUrl}/api/stocks/sectors`, {
                timeout: 45000
            });

            if (response.data && Array.isArray(response.data) && response.data.length > 0) {
                this.renderSectorBubbleChart(response.data);
                this.renderSectorStocksComparison(response.data);
            } else {
                console.warn("섹터 데이터가 비어있습니다. 더미 데이터를 표시합니다.");
                const dummyData = this.generateDummySectorData();
                this.renderSectorBubbleChart(dummyData);
                this.renderSectorStocksComparison(dummyData);
            }
        } catch (error) {
            if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
                console.warn("섹터 데이터 로드 타임아웃: 더미 데이터를 표시합니다.");
            } else {
                console.error("섹터 데이터 로드 실패:", error);
            }
            const dummyData = this.generateDummySectorData();
            this.renderSectorBubbleChart(dummyData);
            this.renderSectorStocksComparison(dummyData);
        }
    }

    generateDummySectorData() {
        return [
            {
                sector: 'Technology',
                stocks: [
                    { symbol: 'AAPL', currentPrice: 175.50, changePercent: 2.30, volume: 50000000, signal: 'buy' },
                    { symbol: 'GOOGL', currentPrice: 142.80, changePercent: 1.80, volume: 30000000, signal: 'hold' },
                    { symbol: 'MSFT', currentPrice: 378.90, changePercent: 2.50, volume: 25000000, signal: 'buy' },
                    { symbol: 'NVDA', currentPrice: 485.20, changePercent: 3.20, volume: 40000000, signal: 'buy' }
                ],
                avgChangePercent: 2.45,
                totalVolume: 145000000,
                avgConfidence: 0.775,
                stockCount: 4
            },
            {
                sector: 'Consumer Discretionary',
                stocks: [
                    { symbol: 'AMZN', currentPrice: 145.30, changePercent: 2.10, volume: 35000000, signal: 'hold' },
                    { symbol: 'TSLA', currentPrice: 245.20, changePercent: 1.80, volume: 60000000, signal: 'hold' }
                ],
                avgChangePercent: 1.95,
                totalVolume: 95000000,
                avgConfidence: 0.675,
                stockCount: 2
            },
            {
                sector: 'Communication Services',
                stocks: [
                    { symbol: 'META', currentPrice: 312.40, changePercent: 1.90, volume: 28000000, signal: 'hold' },
                    { symbol: 'NFLX', currentPrice: 425.60, changePercent: 1.50, volume: 15000000, signal: 'hold' }
                ],
                avgChangePercent: 1.70,
                totalVolume: 43000000,
                avgConfidence: 0.70,
                stockCount: 2
            }
        ];
    }

    renderSectorBubbleChart(sectors) {
        const canvas = document.getElementById('sectorBubbleChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (this.charts.sectorBubble) {
            this.charts.sectorBubble.destroy();
        }

        const colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22'];
        
        const data = sectors.map((sector, index) => {
            const avgChange = sector.avgChangePercent || 0;
            const size = Math.max(20, Math.min(100, Math.abs(avgChange) * 5 + 30));
            return {
                x: index * 30 + 50,
                y: 50,
                r: size,
                label: sector.sector,
                change: avgChange,
                stockCount: sector.stockCount || 0
            };
        });

        this.charts.sectorBubble = new Chart(ctx, {
            type: 'bubble',
            data: {
                datasets: [{
                    label: '섹터',
                    data: data,
                    backgroundColor: data.map((d, i) => {
                        const alpha = d.change >= 0 ? 0.6 : 0.3;
                        return colors[i % colors.length].replace(')', `, ${alpha})`).replace('rgb', 'rgba');
                    }),
                    borderColor: data.map((d, i) => colors[i % colors.length]),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const point = context.raw;
                                return [
                                    `섹터: ${point.label}`,
                                    `평균 변동률: ${point.change >= 0 ? '+' : ''}${point.change.toFixed(2)}%`,
                                    `종목 수: ${point.stockCount}개`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: 100,
                        display: false
                    },
                    y: {
                        min: 0,
                        max: 100,
                        display: false
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const sector = sectors[index];
                        this.showSectorStocks(sector);
                    }
                }
            }
        });
    }

    renderSectorStocksComparison(sectors) {
        const container = document.getElementById('sectorStocksComparison');
        if (!container) return;

        if (sectors.length === 0) {
            container.innerHTML = '<div class="no-data">섹터 데이터가 없습니다.</div>';
            return;
        }

        const sortedSectors = [...sectors].sort((a, b) => (b.avgChangePercent || 0) - (a.avgChangePercent || 0));
        
        const html = sortedSectors.map((sector, index) => {
            const stocks = sector.stocks || [];
            const avgChange = sector.avgChangePercent || 0;
            const changeClass = avgChange >= 0 ? 'positive' : 'negative';
            const changeText = avgChange >= 0 ? `+${avgChange.toFixed(2)}%` : `${avgChange.toFixed(2)}%`;
            const changeIcon = avgChange >= 0 ? '▲' : '▼';
            
            const stocksRows = stocks.map(stock => {
                const stockChange = stock.changePercent || 0;
                const stockChangeClass = stockChange >= 0 ? 'positive' : 'negative';
                const stockChangeText = stockChange >= 0 ? `+${stockChange.toFixed(2)}%` : `${stockChange.toFixed(2)}%`;
                const stockChangeIcon = stockChange >= 0 ? '▲' : '▼';
                const signalClass = stock.signal === 'buy' ? 'signal-buy' : stock.signal === 'sell' ? 'signal-sell' : 'signal-hold';
                const signalText = stock.signal === 'buy' ? '매수' : stock.signal === 'sell' ? '매도' : '보유';
                
                return `
                    <tr class="sector-stock-row">
                        <td class="stock-symbol-cell">
                            <strong>${stock.symbol}</strong>
                        </td>
                        <td class="stock-price-cell">
                            $${stock.currentPrice?.toFixed(2) || '0.00'}
                        </td>
                        <td class="stock-change-cell ${stockChangeClass}">
                            <span class="change-icon">${stockChangeIcon}</span>
                            ${stockChangeText}
                        </td>
                        <td class="stock-signal-cell">
                            <span class="stock-signal ${signalClass}">${signalText}</span>
                        </td>
                    </tr>
                `;
            }).join('');

            return `
                <div class="sector-table-card">
                    <div class="sector-table-header">
                        <div class="sector-title-group">
                            <h4 class="sector-name">${sector.sector}</h4>
                        </div>
                        <div class="sector-stats">
                            <span class="sector-avg-change ${changeClass}">
                                <span class="change-icon">${changeIcon}</span>
                                ${changeText}
                            </span>
                            <span class="sector-count">
                                ${sector.stockCount || 0}개 종목
                            </span>
                        </div>
                    </div>
                    <div class="sector-table-wrapper">
                        <table class="sector-stocks-table">
                            <thead>
                                <tr>
                                    <th>종목</th>
                                    <th>현재가</th>
                                    <th>변동률</th>
                                    <th>신호</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${stocksRows}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = html;
        
        setTimeout(() => {
            this.initSectorSlider();
        }, 100);
    }

    initSectorSlider() {
        const container = document.getElementById('sectorStocksComparison');
        const prevBtn = document.getElementById('sectorSliderPrev');
        const nextBtn = document.getElementById('sectorSliderNext');
        
        if (!container || !prevBtn || !nextBtn) {
            console.warn('슬라이드 요소를 찾을 수 없습니다.');
            return;
        }

        const cards = container.querySelectorAll('.sector-table-card');
        if (cards.length === 0) {
            console.warn('섹터 카드를 찾을 수 없습니다.');
            return;
        }

        if (this.sectorSliderHandlers) {
            prevBtn.removeEventListener('click', this.sectorSliderHandlers.handlePrevClick);
            nextBtn.removeEventListener('click', this.sectorSliderHandlers.handleNextClick);
            window.removeEventListener('resize', this.sectorSliderHandlers.handleResize);
            if (this.sectorSliderHandlers.autoSlideInterval) {
                clearInterval(this.sectorSliderHandlers.autoSlideInterval);
            }
        }

        this.sectorSliderCurrentIndex = 0;
        
        const wrapper = container.parentElement;
        if (!wrapper) {
            console.warn('슬라이더 wrapper를 찾을 수 없습니다.');
            return;
        }
        
        const getCardWidth = () => {
            const wrapperWidth = wrapper.offsetWidth || wrapper.clientWidth || 800;
            const buttonWidth = 44;
            const gap = 12;
            const availableWidth = wrapperWidth - (buttonWidth * 2) - (gap * 2);
            return Math.max(400, availableWidth);
        };
        
        let cardWidth = getCardWidth();
        const maxIndex = cards.length - 1;
        
        cards.forEach((card) => {
            card.style.width = `${cardWidth}px`;
            card.style.minWidth = `${cardWidth}px`;
            card.style.maxWidth = `${cardWidth}px`;
            card.style.flexShrink = '0';
            card.style.flexGrow = '0';
        });
        
        const containerWidth = cardWidth * cards.length;
        container.style.display = 'flex';
        container.style.width = `${containerWidth}px`;
        container.style.height = '100%';
        container.style.flexShrink = '0';
        container.style.flexGrow = '0';
        container.style.transition = 'transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        container.style.transform = 'translateX(0px)';
        container.style.position = 'relative';
        container.style.isolation = 'isolate';
        
        wrapper.style.overflow = 'hidden';
        wrapper.style.position = 'relative';
        wrapper.style.isolation = 'isolate';
        
        const comparisonWidth = wrapper.offsetWidth - (44 * 2) - (12 * 2);
        container.style.maxWidth = `${containerWidth}px`;
        
        const containerParent = container.parentElement;
        if (containerParent && containerParent !== wrapper) {
            containerParent.style.overflow = 'hidden';
        }
        
        const updateSlider = () => {
            const translateX = -this.sectorSliderCurrentIndex * cardWidth;
            container.style.transform = `translateX(${translateX}px)`;
            container.style.willChange = 'transform';
            
            prevBtn.disabled = this.sectorSliderCurrentIndex === 0;
            nextBtn.disabled = this.sectorSliderCurrentIndex >= maxIndex;
            
            prevBtn.style.opacity = this.sectorSliderCurrentIndex === 0 ? '0.3' : '1';
            prevBtn.style.pointerEvents = this.sectorSliderCurrentIndex === 0 ? 'none' : 'auto';
            
            nextBtn.style.opacity = this.sectorSliderCurrentIndex >= maxIndex ? '0.3' : '1';
            nextBtn.style.pointerEvents = this.sectorSliderCurrentIndex >= maxIndex ? 'none' : 'auto';
            
            cards.forEach((card, index) => {
                if (index === this.sectorSliderCurrentIndex) {
                    card.style.visibility = 'visible';
                } else {
                    card.style.visibility = 'hidden';
                }
            });
        };

        const handlePrevClick = () => {
            if (this.sectorSliderCurrentIndex > 0) {
                this.sectorSliderCurrentIndex--;
                updateSlider();
            }
        };

        const handleNextClick = () => {
            if (this.sectorSliderCurrentIndex < maxIndex) {
                this.sectorSliderCurrentIndex++;
                updateSlider();
            }
        };

        const startAutoSlide = () => {
            if (this.sectorSliderHandlers.autoSlideInterval) {
                clearInterval(this.sectorSliderHandlers.autoSlideInterval);
            }
            this.sectorSliderHandlers.autoSlideInterval = setInterval(() => {
                if (this.sectorSliderCurrentIndex < maxIndex) {
                    this.sectorSliderCurrentIndex++;
                } else {
                    this.sectorSliderCurrentIndex = 0;
                }
                updateSlider();
            }, 5000);
        };

        const stopAutoSlide = () => {
            if (this.sectorSliderHandlers.autoSlideInterval) {
                clearInterval(this.sectorSliderHandlers.autoSlideInterval);
                this.sectorSliderHandlers.autoSlideInterval = null;
            }
        };

        const handlePrevClickWithAuto = () => {
            stopAutoSlide();
            handlePrevClick();
            setTimeout(startAutoSlide, 3000);
        };

        const handleNextClickWithAuto = () => {
            stopAutoSlide();
            handleNextClick();
            setTimeout(startAutoSlide, 3000);
        };

        this.sectorSliderHandlers = {
            handlePrevClick: handlePrevClickWithAuto,
            handleNextClick: handleNextClickWithAuto,
            handleResize: null,
            autoSlideInterval: null
        };
        
        prevBtn.addEventListener('click', handlePrevClickWithAuto);
        nextBtn.addEventListener('click', handleNextClickWithAuto);

        wrapper.addEventListener('mouseenter', stopAutoSlide);
        wrapper.addEventListener('mouseleave', startAutoSlide);
        
        let resizeTimer;
        const handleResize = () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                cardWidth = getCardWidth();
                cards.forEach((card) => {
                    card.style.width = `${cardWidth}px`;
                    card.style.minWidth = `${cardWidth}px`;
                    card.style.maxWidth = `${cardWidth}px`;
                });
                const containerWidth = cardWidth * cards.length;
                container.style.width = `${containerWidth}px`;
                container.style.height = '100%';
                container.style.flexShrink = '0';
                container.style.flexGrow = '0';
                container.style.maxWidth = `${containerWidth}px`;
                wrapper.style.overflow = 'hidden';
                wrapper.style.position = 'relative';
                wrapper.style.isolation = 'isolate';
                updateSlider();
            }, 250);
        };
        
        this.sectorSliderHandlers.handleResize = handleResize;
        window.addEventListener('resize', handleResize);

        let isDragging = false;
        let startX = 0;
        let scrollLeft = 0;

        const handleMouseDown = (e) => {
            isDragging = true;
            startX = e.pageX - container.offsetLeft;
            scrollLeft = this.sectorSliderCurrentIndex * cardWidth;
            container.style.cursor = 'grabbing';
        };

        const handleMouseLeave = () => {
            isDragging = false;
            container.style.cursor = 'grab';
        };

        const handleMouseUp = () => {
            isDragging = false;
            container.style.cursor = 'grab';
        };

        const handleMouseMove = (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - container.offsetLeft;
            const walk = (x - startX) * 2;
            const newIndex = Math.round((scrollLeft - walk) / cardWidth);
            if (newIndex >= 0 && newIndex <= maxIndex && newIndex !== this.sectorSliderCurrentIndex) {
                this.sectorSliderCurrentIndex = newIndex;
                updateSlider();
            }
        };

        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mouseleave', handleMouseLeave);
        container.addEventListener('mouseup', handleMouseUp);
        container.addEventListener('mousemove', handleMouseMove);
        container.style.cursor = 'grab';

        let touchStartX = 0;
        let touchStartY = 0;

        container.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }, { passive: true });

        container.addEventListener('touchend', (e) => {
            if (!touchStartX || !touchStartY) return;
            
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            
            const diffX = touchStartX - touchEndX;
            const diffY = touchStartY - touchEndY;
            
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                if (diffX > 0 && this.sectorSliderCurrentIndex < maxIndex) {
                    this.sectorSliderCurrentIndex++;
                } else if (diffX < 0 && this.sectorSliderCurrentIndex > 0) {
                    this.sectorSliderCurrentIndex--;
                }
                updateSlider();
            }
            
            touchStartX = 0;
            touchStartY = 0;
        }, { passive: true });

        updateSlider();
        
        if (cards.length > 1) {
            startAutoSlide();
        }
    }

    showSectorStocks(sector) {
        const container = document.getElementById('sectorStocksComparison');
        if (!container) return;

        const stocks = sector.stocks || [];
        const html = `
            <div class="sector-detail">
                <div class="sector-detail-header">
                    <h4>${sector.sector} 상세</h4>
                    <button onclick="dashboard.loadSectorsAnalysis()" class="btn-small">전체 보기</button>
                </div>
                <div class="sector-stocks-list">
                    ${stocks.map(stock => {
                        const change = stock.changePercent || 0;
                        const changeClass = change >= 0 ? 'positive' : 'negative';
                        const changeText = change >= 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`;
                        return `
                            <div class="sector-stock-item">
                                <span class="stock-symbol">${stock.symbol}</span>
                                <span class="stock-price">$${stock.currentPrice?.toFixed(2) || '0.00'}</span>
                                <span class="stock-change ${changeClass}">${changeText}</span>
                                <span class="stock-volume">거래량: ${(stock.volume || 0).toLocaleString()}</span>
                                <span class="stock-signal">${stock.signal || 'hold'}</span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
        container.innerHTML = html;
    }

    startHealthCheck() {
        this.healthCheckState = {
            consecutiveFailures: 0,
            checkInterval: 30000,
            isPaused: false,
            lastCheckTime: 0
        };

        setTimeout(() => {
            this.performHealthCheck();
        }, 1000);

        this.scheduleNextHealthCheck();
    }

    async performHealthCheck() {
        const now = Date.now();
        const state = this.healthCheckState;
        
        if (state.isPaused || (now - state.lastCheckTime < state.checkInterval)) {
            this.scheduleNextHealthCheck();
            return;
        }
        
        state.lastCheckTime = now;
        
        try {
            const success = await this.checkSystemHealth().catch(() => false);
            
            if (success) {
                state.consecutiveFailures = 0;
                state.checkInterval = 30000;
                state.isPaused = false;
            } else {
                state.consecutiveFailures++;
                
                if (state.consecutiveFailures >= 3) {
                    state.isPaused = true;
                    state.checkInterval = 300000;
                } else {
                    state.checkInterval = Math.min(30000 + (state.consecutiveFailures * 30000), 120000);
                }
            }
        } catch {
            state.consecutiveFailures++;
            state.checkInterval = Math.min(30000 + (state.consecutiveFailures * 30000), 120000);
        } finally {
            this.scheduleNextHealthCheck();
        }
    }

    scheduleNextHealthCheck() {
        const state = this.healthCheckState;
        
        setTimeout(() => {
            this.performHealthCheck();
        }, state.checkInterval);
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

function initializeWelcomePopup() {
    const popup = document.getElementById('welcomePopup');
    if (!popup) return;
    
    setupPopupNavigation();
    setupPopupCharts();
    setupPopupData();
    setupPopupClose();
    setupPopupCheckboxes();
    
    if (!shouldShowPopup()) {
        popup.style.display = 'none';
        return;
    }
    
    setTimeout(() => {
        popup.classList.add('show');
    }, 500);
}

function shouldShowPopup() {
    if (localStorage.getItem('hideWelcomePopupForever') === 'true') {
        return false;
    }
    
    const hideToday = localStorage.getItem('hideWelcomePopupToday');
    if (hideToday) {
        const today = new Date().toDateString();
        if (hideToday === today) {
            return false;
        } else {
            localStorage.removeItem('hideWelcomePopupToday');
        }
    }
    
    return true;
}

function setupPopupNavigation() {
    const slides = document.querySelectorAll('.popup-slide');
    const dots = document.querySelectorAll('.pagination-dot');
    const prevBtn = document.getElementById('popupPrev');
    const nextBtn = document.getElementById('popupNext');
    
    let currentSlide = 0;
    const totalSlides = slides.length;
    
    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.toggle('active', i === index);
        });
        
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
        
        if (prevBtn) prevBtn.disabled = index === 0;
        if (nextBtn) nextBtn.disabled = index === totalSlides - 1;
        
        currentSlide = index;
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentSlide > 0) {
                showSlide(currentSlide - 1);
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentSlide < totalSlides - 1) {
                showSlide(currentSlide + 1);
            }
        });
    }
    
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            showSlide(index);
        });
    });
    
    showSlide(0);
}

function generateRandomChartData(count) {
    const labels = Array.from({ length: count }, (_, i) => '');
    const baseValue = 100;
    const values = [];
    let currentValue = baseValue;
    
    for (let i = 0; i < count; i++) {
        currentValue += (Math.random() - 0.5) * 2;
        values.push(Math.max(0, currentValue));
    }
    
    return { labels, values };
}

function createIndexChart(canvas) {
    if (!canvas) return;
    
    canvas.style.width = '100%';
    canvas.style.height = '40px';
    canvas.width = canvas.offsetWidth || 200;
    canvas.height = 40;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    ctx.strokeStyle = '#e74c3c';
    ctx.fillStyle = 'rgba(231, 76, 60, 0.1)';
    ctx.lineWidth = 2;
    
    const data = generateRandomChartData(20);
    const max = Math.max(...data.values);
    const min = Math.min(...data.values);
    const range = max - min || 1;
    
    ctx.beginPath();
    data.values.forEach((value, index) => {
        const x = (index / (data.values.length - 1)) * width;
        const y = height - ((value - min) / range) * height;
        
        if (index === 0) {
            ctx.moveTo(x, height);
            ctx.lineTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.lineTo(width, height);
    ctx.closePath();
    ctx.fill();
    
    ctx.beginPath();
    data.values.forEach((value, index) => {
        const x = (index / (data.values.length - 1)) * width;
        const y = height - ((value - min) / range) * height;
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
}

function setupPopupCharts() {
    const chartIds = ['kospiChart', 'kosdaqChart', 'kospi200Chart', 'sp500Chart', 'dowChart', 'nasdaqChart'];
    
    chartIds.forEach(chartId => {
        const canvas = document.getElementById(chartId);
        if (canvas) {
            createIndexChart(canvas);
        }
    });
}

function setupPopupData() {
    setupPopupSectorBubbles();
    setupPopupPopularStocks();
}

function setupPopupSectorBubbles() {
    const bubbleChart = document.getElementById('popupSectorBubbles');
    const stocksList = document.getElementById('popupSectorStocks');
    
    if (!bubbleChart || !stocksList) return;
    
    const sectors = [
        { name: 'Technology', color: '#e74c3c', size: 100, stocks: [
            { name: 'Apple (AAPL)', price: 175.50, change: 2.83, icon: '🍎' },
            { name: 'Google (GOOGL)', price: 142.80, change: 1.25, icon: '🔵' }
        ]},
        { name: 'AI/ML', color: '#3498db', size: 80, stocks: [
            { name: 'Microsoft (MSFT)', price: 378.90, change: 3.15, icon: '⚡' }
        ]},
        { name: 'Energy', color: '#2ecc71', size: 75, stocks: [
            { name: 'Tesla (TSLA)', price: 245.20, change: 1.80, icon: '⛽' }
        ]},
        { name: 'Cloud', color: '#f39c12', size: 70, stocks: [
            { name: 'Amazon (AMZN)', price: 145.30, change: 2.10, icon: '☁️' }
        ]},
        { name: 'Semiconductor', color: '#3498db', size: 65, stocks: [
            { name: 'NVIDIA (NVDA)', price: 485.20, change: 1.50, icon: '💻' }
        ]},
        { name: 'Social Media', color: '#e91e63', size: 60, stocks: [
            { name: 'Meta (META)', price: 312.40, change: 0.95, icon: '📱' }
        ]}
    ];
    
    sectors.forEach((sector, index) => {
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = sector.name;
        bubble.style.width = `${sector.size}px`;
        bubble.style.height = `${sector.size}px`;
        bubble.style.backgroundColor = sector.color;
        bubble.style.left = `${20 + (index % 3) * 30}%`;
        bubble.style.top = `${20 + Math.floor(index / 3) * 35}%`;
        bubble.style.transform = 'translate(-50%, -50%)';
        bubble.style.cursor = 'pointer';
        
        bubble.addEventListener('click', () => {
            displaySectorStocks(sector.stocks, stocksList);
        });
        
        bubbleChart.appendChild(bubble);
    });
    
    if (sectors.length > 0) {
        displaySectorStocks(sectors[0].stocks, stocksList);
    }
}

function displaySectorStocks(stocks, container) {
    if (!container) return;
    
    container.innerHTML = stocks.map(stock => `
        <div class="sector-stock-item">
            <div class="sector-stock-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                ${stock.icon}
            </div>
            <div class="sector-stock-name">${stock.name}</div>
            <div class="sector-stock-price">$${stock.price.toFixed(2)}</div>
            <div class="sector-stock-change ${stock.change >= 0 ? 'positive' : 'negative'}">
                ${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}%
            </div>
        </div>
    `).join('');
}

function setupPopupPopularStocks() {
    const container = document.getElementById('popupPopularStocks');
    if (!container) return;
    
    const popularStocks = [
        { name: 'Apple (AAPL)', price: 175.50, change: 4.04, changePercent: 2.30, icon: 'AAPL' },
        { name: 'Google (GOOGL)', price: 142.80, change: 2.57, changePercent: 1.80, icon: 'GOOGL' },
        { name: 'Microsoft (MSFT)', price: 378.90, change: 9.47, changePercent: 2.50, icon: 'MSFT' },
        { name: 'NVIDIA (NVDA)', price: 485.20, change: 15.05, changePercent: 3.20, icon: 'NVDA' },
        { name: 'Meta (META)', price: 312.40, change: 5.94, changePercent: 1.90, icon: 'META' }
    ];
    
    container.innerHTML = popularStocks.map(stock => `
        <div class="popular-stock-item">
            <div class="popular-stock-icon">${stock.icon.substring(0, 2)}</div>
            <div class="popular-stock-info">
                <div class="popular-stock-name">${stock.name}</div>
                <div class="popular-stock-price">$${stock.price.toFixed(2)}</div>
            </div>
            <div class="popular-stock-change ${stock.change >= 0 ? 'positive' : 'negative'}">
                ${stock.change >= 0 ? '+' : ''}$${stock.change.toFixed(2)} ${stock.changePercent >= 0 ? '+' : ''}${stock.changePercent.toFixed(2)}%
            </div>
            <div class="popular-stock-star">⭐</div>
        </div>
    `).join('');
}

function setupPopupClose() {
    const closeBtn = document.getElementById('popupClose');
    const popup = document.getElementById('welcomePopup');
    
    if (closeBtn && popup) {
        closeBtn.addEventListener('click', () => {
            closePopup();
        });
    }
    
    if (popup) {
        popup.addEventListener('click', (e) => {
            if (e.target === popup) {
                closePopup();
            }
        });
    }
}

function closePopup() {
    const popup = document.getElementById('welcomePopup');
    if (popup) {
        popup.classList.remove('show');
        setTimeout(() => {
            popup.style.display = 'none';
        }, 300);
    }
}

function setupPopupCheckboxes() {
    const hideToday = document.getElementById('hideToday');
    const hideForever = document.getElementById('hideForever');
    
    if (hideToday) {
        hideToday.addEventListener('change', (e) => {
            if (e.target.checked) {
                const today = new Date().toDateString();
                localStorage.setItem('hideWelcomePopupToday', today);
                if (hideForever) hideForever.checked = false;
            } else {
                localStorage.removeItem('hideWelcomePopupToday');
            }
        });
    }
    
    if (hideForever) {
        hideForever.addEventListener('change', (e) => {
            if (e.target.checked) {
                localStorage.setItem('hideWelcomePopupForever', 'true');
                if (hideToday) hideToday.checked = false;
            } else {
                localStorage.removeItem('hideWelcomePopupForever');
            }
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    dashboard = new StockDashboard();
    window.dashboard = dashboard;
    
    initializeWelcomePopup();
});