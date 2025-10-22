#!/bin/bash

echo "Spring Boot 서버를 시작합니다..."
echo "포트: 8080"
echo "종료하려면 Ctrl+C를 누르세요"
echo "----------------------------------------"

cd spring-stock-dashboard

./gradlew bootRun
