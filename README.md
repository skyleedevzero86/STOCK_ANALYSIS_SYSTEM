<img width="1020" height="678" alt="image" src="https://github.com/user-attachments/assets/3b0ad1f1-06a1-4fe5-923c-99ccfd521419" /><br/>

# 실시간 주식 데이터 분석 및 알림 시스템

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.2.0-green.svg)](https://spring.io/projects/spring-boot)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-teal.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](https://opensource.org/licenses/Apache-2.0)

## 프로젝트 개요

**Stock Analysis System**은 실시간 주식 데이터 수집, 고급 기술적 분석, AI 기반 인사이트 생성, 그리고 종합적인 알림 시스템을 제공하는 마이크로서비스 기반의 종합 투자 플랫폼입니다.

## 화면

<img width="1888" height="951" alt="image" src="https://github.com/user-attachments/assets/eb7ac3d0-dcd4-4fa3-9ada-d07a06b2e06d" /><br/>
<img width="1268" height="953" alt="image" src="https://github.com/user-attachments/assets/088e7d3d-f009-4006-81c2-2bbe06647323" /><br/>

### 핵심 특징

- **실시간 데이터 처리**: Yahoo Finance, Alpha Vantage API를 통한 실시간 주가 데이터 수집
- **고급 기술적 분석**: RSI, MACD, 볼린저 밴드 등 20+ 기술적 지표 계산
- **AI 기반 분석**: 머신러닝을 활용한 이상 패턴 감지 및 투자 인사이트 생성
- **마이크로서비스 아키텍처**: Python FastAPI + Spring Boot 기반 확장 가능한 구조
- **실시간 대시보드**: WebSocket을 통한 실시간 차트 및 분석 결과 시각화
- **이메일 알림 시스템**: AI 기반 이메일 템플릿을 통한 개인화된 알림

## 시스템 아키텍처

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Dashboard]
        API_CLIENT[API Client]
    end

    subgraph "API Gateway Layer"
        SPRING[Spring Boot Server<br/>Port 8080]
        PYTHON_API[Python FastAPI Server<br/>Port 9000]
        PYTHON_ENHANCED[Enhanced Python API<br/>Port 8001]
        AIRFLOW[Apache Airflow<br/>Port 8081]
    end

    subgraph "Service Layer"
        DATA_COLLECTOR[Data Collector Service]
        ANALYSIS_ENGINE[Analysis Engine]
        AI_SERVICE[AI Analysis Service]
        NOTIFICATION[Notification Service]
    end

    subgraph "Data Layer"
        MYSQL[(MySQL Database)]
        REDIS[(Redis Cache)]
    end

    subgraph "External APIs"
        ALPHA_VANTAGE[Alpha Vantage API]
        YAHOO[Yahoo Finance API]
        SMTP[SMTP Server]
    end

    WEB --> SPRING
    API_CLIENT --> PYTHON_API
    API_CLIENT --> PYTHON_ENHANCED
    SPRING --> PYTHON_API
    SPRING --> PYTHON_ENHANCED
    AIRFLOW --> SPRING
    AIRFLOW --> PYTHON_API
    PYTHON_API --> DATA_COLLECTOR
    PYTHON_ENHANCED --> DATA_COLLECTOR
    PYTHON_API --> ANALYSIS_ENGINE
    PYTHON_ENHANCED --> ANALYSIS_ENGINE
    PYTHON_ENHANCED --> AI_SERVICE
    PYTHON_API --> NOTIFICATION
    PYTHON_ENHANCED --> NOTIFICATION
    DATA_COLLECTOR --> ALPHA_VANTAGE
    DATA_COLLECTOR --> YAHOO
    NOTIFICATION --> SMTP
    PYTHON_API --> MYSQL
    PYTHON_ENHANCED --> MYSQL
    PYTHON_ENHANCED --> REDIS
    SPRING --> MYSQL
```

## 주요 기능

### 1. 실시간 데이터 수집

- **다중 API 지원**: Yahoo Finance, Alpha Vantage API
- **성능 최적화**: 비동기 처리, 캐싱, Rate Limiting
- **데이터 품질 관리**: 자동 검증 및 품질 점수 계산
- **Fallback 메커니즘**: API 장애 시 자동 대체 수집
- **뉴스 데이터 수집**: 주식 관련 뉴스 자동 수집 및 분석

### 2. 고급 기술적 분석

- **기본 지표**: RSI, MACD, 볼린저 밴드, 이동평균선
- **고급 지표**: ADX, Stochastic, Williams %R, MFI
- **패턴 인식**: 차트 패턴 자동 감지
- **지지/저항선**: 자동 계산 및 분석
- **피보나치 레벨**: 자동 피보나치 되돌림 분석

### 3. AI 기반 분석

- **이상 패턴 감지**: Isolation Forest, K-Means 클러스터링
- **시장 상황 분석**: 트렌드 강도, 시장 체제 분석
- **투자 신호 생성**: AI 기반 매수/매도/보유 신호
- **신뢰도 점수**: 분석 결과의 신뢰도 정량화

### 4. 실시간 대시보드

- **인터랙티브 차트**: Chart.js 기반 실시간 차트
- **WebSocket 통신**: 실시간 데이터 스트리밍
- **반응형 디자인**: 모바일/데스크톱 최적화
- **다국어 지원**: 한국어/영어 지원

### 5. 이메일 구독 및 알림 시스템

- **이메일 구독**: 사용자가 이메일 구독 신청 및 관리
- **개인화 알림**: 사용자별 알림 조건 및 템플릿 설정
- **AI 템플릿**: 동적 이메일 템플릿 생성 및 변수 치환
- **자동 발송**: Airflow DAG를 통한 일일 리포트 자동 발송
- **관리자 대시보드**: 구독자 관리 및 통계 확인
- **개인정보 보호**: 이메일/전화번호 마스킹 처리
- **발송 이력 관리**: 이메일 발송 로그 및 통계 확인

### 6. 뉴스 수집 및 분석

- **다중 뉴스 소스**: NewsAPI, Alpha Vantage, Yahoo Finance, Google News RSS, Naver 뉴스
- **자동 번역**: 한국어 뉴스 자동 번역 지원
- **뉴스 검색**: 키워드 기반 뉴스 검색 기능
- **캐싱**: 뉴스 데이터 캐싱으로 성능 최적화
- **실시간 수집**: 주식 심볼별 관련 뉴스 실시간 수집

### 7. 고객 문의 관리

- **문의 작성**: 사용자 문의 작성 및 제출
- **문의 목록**: 문의 내역 조회 및 관리
- **관리자 답변**: 관리자 답변 작성 및 발송
- **이메일 알림**: 문의 등록 및 답변 시 이메일 알림
- **상태 관리**: 문의 상태 추적 (대기/처리중/완료)

### 8. 보안 및 모니터링

- **JWT 인증**: 토큰 기반 인증 시스템 (Spring Boot, Enhanced API)
- **Rate Limiting**: API 호출 제한 및 IP 차단
- **Circuit Breaker**: 장애 격리 및 복구
- **보안 관리**: 비밀번호 암호화, XSS/SQL Injection 방어
- **세션 관리**: 세션 타임아웃 및 IP 검증
- **로깅 시스템**: 종합적인 로그 관리 및 오류 추적
- **사용자 관리**: 역할 기반 접근 제어 (RBAC)
- **권한 관리**: 세밀한 권한 관리 시스템

## 폴더 구조

```
StockAnalysisSystem/
├── python/                  # Python 백엔드 서비스
│   ├── data_collectors/     # 데이터 수집 모듈
│   │   ├── stock_data_collector.py
│   │   ├── performance_optimized_collector.py
│   │   └── news_collector.py
│   ├── analysis_engine/     # 분석 엔진
│   │   ├── technical_analyzer.py
│   │   └── advanced_analyzer.py
│   ├── airflow_dags/        # Airflow DAG들
│   │   ├── stock_analysis_dag.py
│   │   └── email_notification_dag.py
│   ├── notification/        # 알림 서비스
│   │   └── notification_service.py
│   ├── database/            # DB 스키마
│   │   ├── schema.sql
│   │   └── sample_notification_settings.sql
│   ├── config/              # 설정 파일
│   │   ├── settings.py
│   │   └── logging_config.py
│   ├── security/            # 보안 모듈
│   │   └── security_manager.py
│   ├── error_handling/      # 오류 처리
│   │   └── error_manager.py
│   ├── utils/               # 유틸리티 모듈
│   │   ├── data_formatter.py
│   │   ├── db_checker.py
│   │   ├── http_client.py
│   │   ├── notification_logger.py
│   │   ├── print_utils.py
│   │   ├── retry_handler.py
│   │   └── service_checker.py
│   ├── tests/               # 테스트 코드
│   │   ├── test_api_server.py
│   │   ├── test_api_server_enhanced.py
│   │   ├── test_technical_analyzer.py
│   │   ├── test_advanced_analyzer.py
│   │   ├── test_notification_service.py
│   │   ├── test_stock_data_collector.py
│   │   ├── test_performance_optimized_collector.py
│   │   ├── test_security_manager.py
│   │   ├── test_error_manager.py
│   │   ├── test_integration.py
│   │   ├── test_e2e.py
│   │   └── test_performance.py
│   ├── docs/                # 문서
│   │   ├── SYSTEM_ARCHITECTURE.md
│   │   ├── API_DOCUMENTATION.md
│   │   ├── INTEGRATION_GUIDE.md
│   │   ├── TECHNICAL_INDICATORS_GUIDE.md
│   │   ├── TESTING_GUIDE.md
│   │   ├── openapi.yaml
│   │   └── adr/             # 아키텍처 결정 기록
│   │       ├── 001-microservices-architecture.md
│   │       ├── 002-data-collection-strategy.md
│   │       ├── 003-technical-analysis-engine.md
│   │       ├── 004-real-time-data-streaming.md
│   │       ├── 005-database-strategy.md
│   │       ├── 006-notification-system.md
│   │       └── 007-ai-analysis-integration.md
│   ├── api_server_enhanced.py  # 향상된 Python API 서버 (Port 8001)
│   ├── api_common.py        # 공통 API 유틸리티
│   ├── main.py              # 메인 실행 파일
│   ├── start_python_api.py  # Python API 서버 실행 스크립트
│   ├── requirements.txt     # Python 의존성
│   ├── pytest.ini           # pytest 설정
│   ├── env_example.txt      # 환경 변수 예제
│   ├── exceptions.py        # 커스텀 예외 클래스
│   ├── check_python_api.py  # Python API 상태 확인
│   ├── check_services.py    # 서비스 상태 확인
│   ├── check_airflow_email.py      # Airflow 이메일 확인
│   ├── check_auto_email.py         # 자동 이메일 확인
│   ├── diagnose_email_sending.py  # 이메일 발송 진단
│   ├── test_email_send.py         # 이메일 발송 테스트
│   ├── test_airflow_connection.py # Airflow 연결 테스트
│   ├── install_translation_modules.py  # 번역 모듈 설치
│   └── run_dashboard.py     # 대시보드 실행
├── webbackend/              # Spring Boot 백엔드
│   ├── src/main/kotlin/com/sleekydz86/backend/
│   │   ├── application/     # 애플리케이션 계층
│   │   │   ├── command/     # CQRS Command 핸들러
│   │   │   │   ├── StockCommandHandler.kt
│   │   │   │   ├── AnalyzeStockCommandHandler.kt
│   │   │   │   ├── GenerateTradingSignalCommandHandler.kt
│   │   │   │   └── UpdateStockPriceCommandHandler.kt
│   │   │   ├── controller/  # REST 컨트롤러
│   │   │   │   ├── StockController.kt
│   │   │   │   ├── AdminController.kt
│   │   │   │   ├── AuthController.kt
│   │   │   │   ├── EmailSubscriptionController.kt
│   │   │   │   ├── EmailTemplateController.kt
│   │   │   │   ├── AIAnalysisController.kt
│   │   │   │   ├── AIEmailController.kt
│   │   │   │   ├── NewsController.kt
│   │   │   │   ├── ContactInquiryController.kt
│   │   │   │   ├── UserManagementController.kt
│   │   │   │   ├── RoleManagementController.kt
│   │   │   │   ├── PermissionManagementController.kt
│   │   │   │   ├── ProfileController.kt
│   │   │   │   ├── CacheController.kt
│   │   │   │   ├── HealthController.kt
│   │   │   │   ├── PublicController.kt
│   │   │   │   └── WebController.kt
│   │   │   ├── dto/         # 데이터 전송 객체
│   │   │   │   ├── ApiResponse.kt
│   │   │   │   ├── AuthDto.kt
│   │   │   │   ├── UserDto.kt
│   │   │   │   ├── RoleDto.kt
│   │   │   │   └── PermissionDto.kt
│   │   │   ├── mapper/      # DTO 매퍼
│   │   │   │   ├── UserMapper.kt
│   │   │   │   ├── RoleMapper.kt
│   │   │   │   ├── PermissionMapper.kt
│   │   │   │   └── EmailSubscriptionMapper.kt
│   │   │   └── service/     # 애플리케이션 서비스
│   │   │       └── CachedStockAnalysisService.kt
│   │   ├── domain/          # 도메인 계층
│   │   │   ├── model/       # 도메인 모델
│   │   │   │   ├── StockData.kt
│   │   │   │   ├── TechnicalAnalysis.kt
│   │   │   │   ├── TradingSignals.kt
│   │   │   │   ├── AIAnalysisResult.kt
│   │   │   │   ├── EmailSubscription.kt
│   │   │   │   ├── EmailTemplate.kt
│   │   │   │   ├── User.kt
│   │   │   │   ├── Role.kt
│   │   │   │   ├── Permission.kt
│   │   │   │   ├── News.kt
│   │   │   │   └── ContactInquiry.kt
│   │   │   ├── service/     # 도메인 서비스
│   │   │   ├── repository/  # 리포지토리 인터페이스
│   │   │   ├── cqrs/        # CQRS 패턴
│   │   │   │   ├── command/
│   │   │   │   ├── query/
│   │   │   │   └── event/
│   │   │   └── functional/  # 함수형 유틸리티
│   │   ├── infrastructure/  # 인프라 계층
│   │   │   ├── client/      # 외부 API 클라이언트
│   │   │   ├── repository/  # 리포지토리 구현
│   │   │   ├── entity/      # JPA 엔티티
│   │   │   ├── cache/       # 캐시 구현
│   │   │   ├── service/     # 인프라 서비스
│   │   │   └── event/       # 이벤트 처리
│   │   ├── global/          # 전역 설정 및 유틸리티
│   │   │   ├── config/      # 설정 클래스
│   │   │   ├── security/    # 보안 설정
│   │   │   ├── exception/   # 예외 처리
│   │   │   ├── handler/     # 예외 핸들러
│   │   │   ├── circuitbreaker/  # Circuit Breaker
│   │   │   ├── query/       # Query 핸들러
│   │   │   ├── router/      # 라우터 설정
│   │   │   └── websocket/   # WebSocket 설정
│   │   └── WebbackendApplication.kt  # 메인 애플리케이션
│   └── src/main/resources/
│       ├── application.yml   # 애플리케이션 설정
│       ├── application-cache.yml  # 캐시 설정
│       ├── docker-compose.yml  # Docker Compose 설정
│       └── static/          # 정적 리소스
│           ├── index.html   # 메인 대시보드
│           ├── email-subscription.html  # 이메일 구독 페이지
│           ├── admin-dashboard.html     # 관리자 대시보드
│           ├── admin-login.html         # 관리자 로그인
│           ├── api-view.html            # API 테스트 페이지
│           ├── template-management.html # 템플릿 관리 페이지
│           ├── email-history.html       # 이메일 발송 이력
│           ├── company.html             # 회사 소개
│           ├── contact.html             # 문의하기
│           ├── contact-inquiry-list.html    # 문의 목록
│           ├── contact-inquiry-detail.html  # 문의 상세
│           ├── news-detail.html         # 뉴스 상세
│           ├── privacy.html             # 개인정보 처리방침
│           ├── terms.html               # 이용약관
│           ├── css/                    # 스타일시트
│           │   ├── dashboard.css
│           │   ├── admin-dashboard.css
│           │   ├── admin-login.css
│           │   ├── email-subscription.css
│           │   ├── template-management.css
│           │   ├── api-view.css
│           │   ├── company.css
│           │   ├── contact.css
│           │   ├── news-detail.css
│           │   ├── privacy.css
│           │   ├── terms.css
│           │   └── common.css
│           └── js/                      # JavaScript 파일
│               ├── dashboard.js
│               ├── admin-dashboard.js
│               ├── admin-login.js
│               ├── email-subscription.js
│               ├── template-management.js
│               ├── email-history.js
│               ├── api-view.js
│               ├── contact.js
│               ├── contact-inquiry-list.js
│               ├── contact-inquiry-detail.js
│               ├── news.js
│               ├── news-detail.js
│               ├── auth-menu.js
│               └── url-utils.js
└── README.md                # 프로젝트 문서
```

## 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/skyleedevzero86/StockAnalysisSystem.git
cd StockAnalysisSystem

# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Python 의존성 설치
pip install -r requirements.txt
```

### 2. 데이터베이스 설정

```bash
# MySQL 데이터베이스 생성
mysql -u root -p < python/database/schema.sql

# 환경 변수 설정
cp python/env_example.txt python/.env
# python/.env 파일에서 실제 값들 설정
```

### 3. 서버 실행

#### Spring Boot 서버 (터미널 1)

```bash
# Linux/Mac
chmod +x start_spring_boot.sh
./start_spring_boot.sh

# Windows
start_spring_boot.bat

# 또는 webbackend 디렉토리에서 직접 실행
cd webbackend
./gradlew bootRun
```

#### Python API 서버 (터미널 2)

```bash
cd python

# 기본 API 서버 (Port 9000)
python start_python_api.py

# 향상된 API 서버 (Port 8001)
python api_server_enhanced.py
```

#### Airflow 서버 (터미널 3)

```bash
# Airflow 웹서버
airflow webserver --port 8081

# Airflow 스케줄러 (터미널 4)
airflow scheduler
```

> **참고**: 실행 순서는 Spring Boot → Python API → Airflow 순서입니다. 자세한 내용은 [AIRFLOW_DOCKER_SETUP.md](AIRFLOW_DOCKER_SETUP.md)를 참조하세요.

### 4. 대시보드 접속

#### 웹 인터페이스 (Spring Boot - Port 8080)

**사용자 페이지:**

- **메인 대시보드**: http://localhost:8080
- **이메일 구독**: http://localhost:8080/email-subscription.html
- **회사 소개**: http://localhost:8080/company.html
- **문의하기**: http://localhost:8080/contact.html
- **문의 목록**: http://localhost:8080/contact-inquiry-list.html
- **뉴스 상세**: http://localhost:8080/news-detail.html
- **개인정보 처리방침**: http://localhost:8080/privacy.html
- **이용약관**: http://localhost:8080/terms.html

**관리자 페이지:**

- **관리자 로그인**: http://localhost:8080/admin-login.html
- **관리자 대시보드**: http://localhost:8080/admin-dashboard.html
- **API 테스트**: http://localhost:8080/api-view.html
- **템플릿 관리**: http://localhost:8080/template-management.html
- **이메일 발송 이력**: http://localhost:8080/email-history.html

#### API 문서

- **Python API (기본)**: http://localhost:9000/docs
- **Python API (향상된)**: http://localhost:8001/docs

#### Airflow UI

- **Airflow 대시보드**: http://localhost:8081 (기본 계정: airflow/airflow)

## 기술 스택

### Backend

- **Python 3.8+**: FastAPI, pandas, numpy, scikit-learn
- **Spring Boot 3.2.0**: Kotlin, WebFlux, WebSocket
- **Database**: MySQL 8.0, Redis
- **Message Queue**: Apache Airflow

### Frontend

- **HTML5/CSS3/JavaScript**: 반응형 웹 디자인
- **Chart.js**: 실시간 차트 시각화
- **Axios**: HTTP 클라이언트
- **WebSocket API**: 실시간 통신

### DevOps & Monitoring

- **Apache Airflow**: 워크플로우 자동화
- **Docker**: 컨테이너화 (Airflow Docker Compose 포함)
- **로깅 시스템**: 종합적인 로그 관리 및 오류 추적
- **디버깅 도구**: 시스템 상태 확인 및 진단 스크립트

## 성능 지표

- **데이터 수집**: 8개 종목 동시 처리 (평균 2초)
- **분석 처리**: 50일 데이터 기준 평균 0.5초
- **API 응답**: 평균 200ms 이하 (향상된 API는 캐싱으로 더 빠름)
- **WebSocket**: 실시간 업데이트 (5초 간격)
- **캐시 히트율**: 80% 이상 (향상된 API)
- **동시 연결**: 최대 100개 WebSocket 연결 지원
- **Airflow DAG 실행**: 자동 이메일 발송

## 주요 페이지

### 웹 인터페이스 (Spring Boot - Port 8080)

#### 사용자 페이지

- **메인 대시보드** (`/index.html`): 실시간 주식 분석 차트
- **이메일 구독** (`/email-subscription.html`): 사용자 구독 신청 페이지
- **회사 소개** (`/company.html`): 회사 정보 및 서비스 소개
- **문의하기** (`/contact.html`): 고객 문의 작성 페이지
- **문의 목록** (`/contact-inquiry-list.html`): 문의 내역 조회
- **문의 상세** (`/contact-inquiry-detail.html`): 문의 상세 보기
- **뉴스 상세** (`/news-detail.html`): 주식 관련 뉴스 상세 보기
- **개인정보 처리방침** (`/privacy.html`): 개인정보 보호 정책
- **이용약관** (`/terms.html`): 서비스 이용약관

#### 관리자 페이지

- **관리자 로그인** (`/admin-login.html`): 관리자 인증 페이지
- **관리자 대시보드** (`/admin-dashboard.html`): 구독자 관리 및 통계
- **API 테스트** (`/api-view.html`): API 엔드포인트 테스트 도구
- **템플릿 관리** (`/template-management.html`): AI 기반 이메일 템플릿 관리
- **이메일 발송 이력** (`/email-history.html`): 이메일 발송 로그 및 통계

### 추가 문서

- **[AIRFLOW_DOCKER_SETUP.md](AIRFLOW_DOCKER_SETUP.md)**: Airflow Docker 설정 가이드
- **[AI_TEMPLATE_GUIDE.md](AI_TEMPLATE_GUIDE.md)**: AI 분석 템플릿 시스템 가이드
- **[docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)**: 전체 API 문서
- **[docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)**: 시스템 아키텍처 상세 설명
- **[docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)**: 통합 가이드
- **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)**: 테스트 가이드
- **[docs/TECHNICAL_INDICATORS_GUIDE.md](docs/TECHNICAL_INDICATORS_GUIDE.md)**: 기술적 지표 가이드
- **[docs/adr/](docs/adr/)**: 아키텍처 결정 기록 (ADR)

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이선스

이 프로젝트는 Apache 2.0 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 연락처

- **프로젝트 링크**: [https://github.com/skyleedevzero86/StockAnalysisSystem](https://github.com/skyleedevzero86/StockAnalysisSystem)
- **이슈 리포트**: [Issues](https://github.com/skyleedevzero86/StockAnalysisSystem/issues)

## 감사의 말

- [Yahoo Finance](https://finance.yahoo.com/) - 실시간 주가 데이터 제공
- [Alpha Vantage](https://www.alphavantage.co/) - 금융 데이터 API
- [FastAPI](https://fastapi.tiangolo.com/) - 고성능 Python 웹 프레임워크
- [Spring Boot](https://spring.io/projects/spring-boot) - 엔터프라이즈 Java 프레임워크

---

```

```
