
# import subprocess
# import sys
# import os

# def run_dashboard():
#     try:
#         print("주식 분석 대시보드를 시작합니다...")
#         print("브라우저에서 http://localhost:8501 을 열어주세요")
#         print("종료하려면 Ctrl+C를 누르세요")
#         print("-" * 50)
#         
#         subprocess.run([
#             sys.executable, "-m", "streamlit", "run", 
#             "web_dashboard/dashboard.py",
#             "--server.port", "8501",
#             "--server.address", "0.0.0.0"
#         ])
#         
#     except KeyboardInterrupt:
#         print("\n대시보드가 종료되었습니다.")
#     except Exception as e:
#         print(f"대시보드 실행 중 오류: {str(e)}")

# if __name__ == "__main__":
#     run_dashboard()

print("파이썬 대시보드는 스프링에서 구현되었습니다.")
print("스프링 서버를 실행하려면: ./start_spring_boot.sh 또는 start_spring_boot.bat")
print("브라우저에서 http://localhost:8080 을 열어주세요")
