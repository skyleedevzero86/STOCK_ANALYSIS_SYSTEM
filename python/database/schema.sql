

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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_email (user_email),
    INDEX idx_symbol (symbol),
    INDEX idx_active (is_active)
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
    error_message TEXT,                 -- 오류 메시지
    INDEX idx_user_email (user_email),
    INDEX idx_symbol (symbol),
    INDEX idx_notification_type (notification_type),
    INDEX idx_status (status),
    INDEX idx_sent_at (sent_at)
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
    INDEX idx_email (email),
    INDEX idx_active (is_active)
);

-- 사용자 테이블 (Spring Boot 백엔드용)
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_active (is_active)
);

-- 권한(Permission) 테이블
CREATE TABLE IF NOT EXISTS permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    resource VARCHAR(100),
    action VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_resource (resource),
    INDEX idx_active (is_active)
);

-- 역할(Role) 테이블
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_active (is_active)
);

-- 사용자-역할 조인 테이블
CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id)
);

-- 역할-권한 조인 테이블
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id)
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

-- 이메일 템플릿 테이블
CREATE TABLE IF NOT EXISTS email_templates (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active)
);

-- AI 분석 결과 테이블
CREATE TABLE IF NOT EXISTS ai_analysis_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    ai_summary TEXT NOT NULL,
    technical_analysis JSON,
    market_sentiment VARCHAR(20),
    risk_level VARCHAR(20),
    recommendation VARCHAR(20),
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_analysis_type (analysis_type),
    INDEX idx_created_at (created_at)
);

-- 기본 관리자 계정 생성 (비밀번호: 1234)
INSERT INTO admin_users (email, password_hash) VALUES
('admin@admin.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDi')
ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash);

-- 기본 권한 생성
INSERT INTO permissions (name, description, resource, action) VALUES
('STOCK_READ', 'Read stock data', 'stock', 'read'),
('STOCK_WRITE', 'Write stock data', 'stock', 'write'),
('ANALYSIS_READ', 'Read analysis data', 'analysis', 'read'),
('ANALYSIS_WRITE', 'Write analysis data', 'analysis', 'write'),
('USER_READ', 'Read user data', 'user', 'read'),
('USER_WRITE', 'Write user data', 'user', 'write'),
('ADMIN_READ', 'Read admin data', 'admin', 'read'),
('ADMIN_WRITE', 'Write admin data', 'admin', 'write'),
('EMAIL_READ', 'Read email data', 'email', 'read'),
('EMAIL_WRITE', 'Write email data', 'email', 'write'),
('TEMPLATE_READ', 'Read template data', 'template', 'read'),
('TEMPLATE_WRITE', 'Write template data', 'template', 'write')
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- 기본 역할 생성
INSERT INTO roles (name, description) VALUES
('USER', 'Regular user role'),
('ADMIN', 'Administrator role')
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- 역할에 권한 할당 (USER 역할)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'USER'
  AND p.resource IN ('stock', 'analysis', 'email')
ON DUPLICATE KEY UPDATE role_id = VALUES(role_id);

-- 역할에 권한 할당 (ADMIN 역할 - 모든 권한)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'ADMIN'
ON DUPLICATE KEY UPDATE role_id = VALUES(role_id);

-- 기본 관리자 사용자 생성 (username: admin, password: admin123)
-- 참고: 실제 프로덕션 환경에서는 DataInitializer.kt에서 처리하므로 이 INSERT는 선택사항입니다.
INSERT INTO users (username, email, password, first_name, last_name, is_active, is_email_verified)
SELECT 'admin', 'admin@stockanalysis.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDi', 'Admin', 'User', TRUE, TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
ON DUPLICATE KEY UPDATE email = VALUES(email);

-- 기본 일반 사용자 생성 (username: user, password: user123)
-- 참고: 실제 프로덕션 환경에서는 DataInitializer.kt에서 처리하므로 이 INSERT는 선택사항입니다.
INSERT INTO users (username, email, password, first_name, last_name, is_active, is_email_verified)
SELECT 'user', 'user@stockanalysis.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDi', 'Regular', 'User', TRUE, TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'user')
ON DUPLICATE KEY UPDATE email = VALUES(email);

-- 사용자에게 역할 할당 (admin -> ADMIN)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.username = 'admin' AND r.name = 'ADMIN'
ON DUPLICATE KEY UPDATE user_id = VALUES(user_id);

-- 사용자에게 역할 할당 (user -> USER)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.username = 'user' AND r.name = 'USER'
ON DUPLICATE KEY UPDATE user_id = VALUES(user_id);

-- 기본 이메일 템플릿 생성
INSERT INTO email_templates (name, subject, content) VALUES
('기본 분석 리포트', '주식 분석 리포트 - {date}', 
'안녕하세요, {name}님!

다음은 {symbol} 종목에 대한 분석 결과입니다:

{ai_analysis}

기술적 분석:
- 현재가: {current_price}
- 변동률: {change_percent}%
- RSI: {rsi}
- MACD: {macd}
- 트렌드: {trend}

시장 심리: {market_sentiment}
리스크 레벨: {risk_level}
투자 추천: {recommendation}
신뢰도: {confidence_score}%

더 자세한 분석은 대시보드에서 <a href="http://localhost:8080">확인</a>하세요

주식 분석 시스템'),
('간단 분석 리포트', '간단 분석 - {symbol}', 
'안녕하세요, {name}님!

다음은 {symbol} 종목에 대한 분석 결과입니다:
{ai_analysis}

현재가: {current_price} ({change_percent}%)
추천: {recommendation}

더 자세한 분석은 대시보드에서 <a href="http://localhost:8080">확인</a>하세요

주식 분석 시스템')
ON DUPLICATE KEY UPDATE content = VALUES(content);