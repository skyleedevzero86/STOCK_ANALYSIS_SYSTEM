#!/usr/bin/env python3

import subprocess
import sys
import os

def run_dashboard():
    try:
        print("주식 분석 대시보드를 시작합니다...")
        print("브라우저에서 http://localhost:8501 을 열어주세요")
        print("종료하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "web_dashboard/dashboard.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
        
    except KeyboardInterrupt:
        print("\n대시보드가 종료되었습니다.")
    except Exception as e:
        print(f"대시보드 실행 중 오류: {str(e)}")

if __name__ == "__main__":
    run_dashboard()
