import sys
from utils.http_client import HttpClient, ServiceStatus
from utils.print_utils import PrintFormatter

def check_python_api(port=9000):
    base_url = f"http://localhost:{port}"
    
    PrintFormatter.print_header("Python API 서버 상태 확인")
    print(f"서버 URL: {base_url}")
    print(PrintFormatter.divider())
    
    print("\n1. 헬스 체크...")
    health_response = HttpClient.check_health(base_url)
    if health_response.status == ServiceStatus.ONLINE:
        print("   서버가 정상 실행 중입니다")
        print(f"   응답: {health_response.data}")
    else:
        PrintFormatter.print_error("서버", health_response.error or "연결 실패")
        print(f"   Python API 서버를 시작하세요: python start_python_api.py")
        return False
    
    print("\n2. 종목 목록 확인...")
    symbols_response = HttpClient.get(f"{base_url}/api/symbols")
    if symbols_response.status == ServiceStatus.ONLINE:
        symbols = symbols_response.data.get('symbols', []) if isinstance(symbols_response.data, dict) else []
        print(f"   사용 가능한 종목: {len(symbols)}개")
        print(f"   종목: {', '.join(symbols[:5])}...")
        test_symbol = symbols[0] if symbols else "AAPL"
    else:
        print(f"   종목 목록 조회 실패")
        test_symbol = "AAPL"
    
    print(f"\n3. 실시간 데이터 확인 ({test_symbol})...")
    realtime_response = HttpClient.get(f"{base_url}/api/realtime/{test_symbol}", timeout=10)
    if realtime_response.status == ServiceStatus.ONLINE:
        data = realtime_response.data
        print("   실시간 데이터 조회 성공")
        print(f"   - 심볼: {data.get('symbol', 'N/A')}")
        print(f"   - 현재가: ${data.get('currentPrice', data.get('price', 0)):.2f}")
        print(f"   - 변동률: {data.get('changePercent', data.get('change_percent', 0)):.2f}%")
        print(f"   - 거래량: {data.get('volume', 0):,}")
    else:
        PrintFormatter.print_error("실시간 데이터", realtime_response.error or "조회 실패")
    
    print(f"\n4. 기술적 분석 데이터 확인 ({test_symbol})...")
    print("   (RSI, MACD 값 확인)")
    analysis_response = HttpClient.get(f"{base_url}/api/analysis/{test_symbol}", timeout=15)
    if analysis_response.status == ServiceStatus.ONLINE:
        data = analysis_response.data
        signals = data.get('signals', {})
        
        print("   기술적 분석 데이터 조회 성공")
        print(f"   - 심볼: {data.get('symbol', 'N/A')}")
        print(f"   - 트렌드: {data.get('trend', 'N/A')}")
        print(f"   - 트렌드 강도: {data.get('trendStrength', data.get('trend_strength', 0)):.2f}")
        
        rsi = signals.get('rsi')
        macd = signals.get('macd')
        macd_signal = signals.get('macdSignal') or signals.get('macd_signal')
        
        print(f"   RSI: {rsi:.2f}" if rsi and rsi != 0 else f"   RSI: {rsi} (데이터 없음!)")
        print(f"   MACD: {macd:.4f}" if macd and macd != 0 else f"   MACD: {macd} (데이터 없음!)")
        print(f"   MACD Signal: {macd_signal:.4f}" if macd_signal and macd_signal != 0 else f"   MACD Signal: {macd_signal} (데이터 없음)")
        
        if (rsi is None or rsi == 0) and (macd is None or macd == 0):
            print("\n   문제 발견: RSI와 MACD 데이터가 없습니다!")
            print("   원인 분석:")
            print("   1. Python API 서버가 정상 실행 중인지 확인")
            print("   2. 과거 데이터가 충분한지 확인 (최소 50일 필요)")
            print("   3. technical_analyzer.py의 calculate_all_indicators가 정상 작동하는지 확인")
            return False
        else:
            print("\n   RSI와 MACD 데이터가 정상적으로 계산되었습니다!")
            return True
    else:
        PrintFormatter.print_error("기술적 분석", analysis_response.error or "조회 실패")
        return False
    
    print(f"\n5. 과거 데이터 확인 ({test_symbol}, 30일)...")
    historical_response = HttpClient.get(f"{base_url}/api/historical/{test_symbol}?days=30", timeout=10)
    if historical_response.status == ServiceStatus.ONLINE:
        data = historical_response.data
        chart_data = data.get('data', []) if isinstance(data, dict) else []
        print(f"   과거 데이터 조회 성공: {len(chart_data)}개 데이터 포인트")
        if len(chart_data) > 0:
            last_point = chart_data[-1]
            print(f"   - 최근 날짜: {last_point.get('date', 'N/A')}")
            print(f"   - 최근 가격: ${last_point.get('close', 0):.2f}")
            print(f"   - 최근 RSI: {last_point.get('rsi', 'N/A')}")
            print(f"   - 최근 MACD: {last_point.get('macd', 'N/A')}")
    else:
        PrintFormatter.print_error("과거 데이터", historical_response.error or "조회 실패")
    
    print(PrintFormatter.header("확인 완료!"))
    return True

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    success = check_python_api(port)
    sys.exit(0 if success else 1)

