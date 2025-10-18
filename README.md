# 실시간 주식 데이터 분석 및 알림 시스템

## 프로젝트 개요

- **목적**: 실시간 주식 데이터 수집, 분석, 알림을 통한 투자 인사이트 제공
- **기술스택**: Python, FastAPI, Airflow, MySQL, Redis, WebSocket
- **특징**:
  - 실시간 데이터 수집 및 처리
  - 기술적 분석 지표 계산
  - 이상 거래량/가격 변동 감지
  - 웹 대시보드 및 알림 서비스

## 시스템 아키텍처

<img width="1020" height="678" alt="image" src="https://github.com/user-attachments/assets/3b0ad1f1-06a1-4fe5-923c-99ccfd521419" />

## 주요 기능

1. **실시간 데이터 수집**: Yahoo Finance, Alpha Vantage API 활용
2. **기술적 분석**: RSI, MACD, 볼린저 밴드 등
3. **이상 패턴 감지**: 거래량 급증, 가격 급등락 감지
4. **알림 시스템**: 이메일, 슬랙, 텔레그램 알림
5. **웹 대시보드**: 실시간 차트 및 분석 결과 시각화

## 폴더 구조

```
Python/
├── data_collectors/     # 데이터 수집 모듈
├── analysis_engine/     # 분석 엔진
├── notification/        # 알림 시스템
├── web_dashboard/       # 웹 대시보드
├── airflow_dags/       # Airflow DAG들
├── database/           # DB 스키마 및 마이그레이션
├── config/             # 설정 파일
└── requirements.txt    # 의존성
```

