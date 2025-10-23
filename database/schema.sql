
-- 주식 분석 시스템 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS stock_analysis;
USE stock_analysis;

-- 주식 기본 정보 테이블
CREATE TABLE IF NOT EXISTS stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,  -- 주식 심볼 (예: AAPL, GOOGL)
    name VARCHAR(100),                    -- 회사명
    sector VARCHAR(50),                   -- 섹터 (예: Technology, Healthcare)
    market_cap BIGINT,                    -- 시가총액
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 일일 주식 가격 데이터 테이블
CREATE TABLE IF NOT EXISTS stock_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,         -- 주식 심볼
    trade_date DATE NOT NULL,            -- 거래일
    open_price DECIMAL(10,2),            -- 시가
    high_price DECIMAL(10,2),            -- 고가
    low_price DECIMAL(10,2),             -- 저가
    close_price DECIMAL(10,2),           -- 종가
    volume BIGINT,                       -- 거래량
    adjusted_close DECIMAL(10,2),        -- 수정종가 (배당, 분할 등 반영)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_date (symbol, trade_date),
    UNIQUE KEY unique_symbol_date (symbol, trade_date)
);

-- 실시간 주식 가격 데이터 테이블
CREATE TABLE IF NOT EXISTS realtime_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,         -- 주식 심볼
    timestamp DATETIME NOT NULL,         -- 실시간 타임스탬프
    price DECIMAL(10,2),                 -- 실시간 가격
    volume BIGINT,                       -- 실시간 거래량
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_timestamp (symbol, timestamp)
);

-- 기술적 지표 데이터 테이블
CREATE TABLE IF NOT EXISTS technical_indicators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,         -- 주식 심볼
    analysis_date DATE NOT NULL,         -- 분석일
    rsi_14 DECIMAL(5,2),                 -- RSI (14일)
    macd DECIMAL(10,4),                  -- MACD
    macd_signal DECIMAL(10,4),           -- MACD 시그널
    macd_histogram DECIMAL(10,4),        -- MACD 히스토그램
    bb_upper DECIMAL(10,2),              -- 볼린저 밴드 상단
    bb_middle DECIMAL(10,2),             -- 볼린저 밴드 중간
    bb_lower DECIMAL(10,2),              -- 볼린저 밴드 하단
    sma_20 DECIMAL(10,2),                -- 단순이동평균 20일
    sma_50 DECIMAL(10,2),                -- 단순이동평균 50일
    ema_12 DECIMAL(10,2),                -- 지수이동평균 12일
    ema_26 DECIMAL(10,2),                -- 지수이동평균 26일
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_date (symbol, analysis_date),
    UNIQUE KEY unique_symbol_date (symbol, analysis_date)
);

-- 이상 패턴 감지 데이터 테이블
CREATE TABLE IF NOT EXISTS anomaly_detections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,         -- 주식 심볼
    detection_type ENUM('volume_spike', 'price_spike', 'rsi_extreme', 'macd_signal') NOT NULL,  -- 감지 유형
    detection_time DATETIME NOT NULL,     -- 감지 시간
    current_value DECIMAL(10,2),         -- 현재 값
    threshold_value DECIMAL(10,2),       -- 임계값
    severity ENUM('low', 'medium', 'high') NOT NULL,  -- 심각도
    message TEXT,                        -- 감지 메시지
    is_notified BOOLEAN DEFAULT FALSE,   -- 알림 발송 여부
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_time (symbol, detection_time),
    INDEX idx_detection_type (detection_type)
);

-- 알림 설정 테이블
CREATE TABLE IF NOT EXISTS notification_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(100) NOT NULL,   -- 사용자 이메일
    symbol VARCHAR(10),                 -- 특정 종목 (NULL이면 전체)
    notification_types JSON,             -- 알림 유형 설정
    rsi_threshold DECIMAL(5,2),         -- RSI 임계값
    volume_spike_threshold DECIMAL(5,2), -- 거래량 급증 임계값
    price_change_threshold DECIMAL(5,2), -- 가격 변동 임계값
    is_active BOOLEAN DEFAULT TRUE,      -- 활성화 여부
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 알림 발송 로그 테이블
CREATE TABLE IF NOT EXISTS notification_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(100) NOT NULL,   -- 수신자 이메일
    symbol VARCHAR(10),                 -- 관련 종목
    notification_type ENUM('email', 'slack', 'telegram') NOT NULL,  -- 알림 유형
    message TEXT,                       -- 발송 메시지
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 발송 시간
    status ENUM('sent', 'failed', 'pending') DEFAULT 'pending',  -- 발송 상태
    error_message TEXT                 -- 오류 메시지
);

-- 일일 분석 요약 테이블
CREATE TABLE IF NOT EXISTS daily_analysis_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,         -- 주식 심볼
    analysis_date DATE NOT NULL,         -- 분석일
    overall_sentiment ENUM('bullish', 'bearish', 'neutral') NOT NULL,  -- 전체 시장 심리
    key_signals JSON,                    -- 주요 신호들
    risk_score DECIMAL(3,2),             -- 리스크 점수 (0.00-1.00)
    recommendation ENUM('buy', 'sell', 'hold') NOT NULL,  -- 투자 추천
    confidence_score DECIMAL(3,2),       -- 신뢰도 점수 (0.00-1.00)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_date (symbol, analysis_date),
    UNIQUE KEY unique_symbol_date (symbol, analysis_date)
);

-- 이메일 구독 테이블
CREATE TABLE IF NOT EXISTS email_subscriptions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    is_email_consent BOOLEAN NOT NULL DEFAULT FALSE,
    is_phone_consent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_email (email),
    INDEX idx_active (is_active)
);

-- 관리자 사용자 테이블
CREATE TABLE IF NOT EXISTS admin_users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_email (email)
);

-- 초기 주식 데이터 삽입 (주요 기술주)
INSERT INTO stocks (symbol, name, sector) VALUES
('AAPL', 'Apple Inc.', 'Technology'),
('GOOGL', 'Alphabet Inc.', 'Technology'),
('MSFT', 'Microsoft Corporation', 'Technology'),
('AMZN', 'Amazon.com Inc.', 'Consumer Discretionary'),
('TSLA', 'Tesla Inc.', 'Consumer Discretionary'),
('NVDA', 'NVIDIA Corporation', 'Technology'),
('META', 'Meta Platforms Inc.', 'Technology'),
('NFLX', 'Netflix Inc.', 'Communication Services')
ON DUPLICATE KEY UPDATE name = VALUES(name), sector = VALUES(sector);

-- 기본 관리자 계정 생성 (비밀번호: 1234)
INSERT INTO admin_users (email, password_hash) VALUES
('admin@admin.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDi')
ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash);
