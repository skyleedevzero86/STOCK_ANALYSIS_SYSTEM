#!/usr/bin/env python3
"""
Python API 서버 상태 확인 스크립트
실제로 RSI와 MACD 데이터가 반환되는지 확인합니다.
"""

import requests
import json
import sys
from datetime import datetime

def check_python_api(port=9000):
    """Python API 서버 상태 확인"""
    base_url = f"http://localhost:{port}"
    
    print("=" * 60)
    print("Python API 서버 상태 확인")
    print("=" * 60)
    print(f"서버 URL: {base_url}")
    print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    print("\n1. 헬스 체크...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("   서버가 정상 실행 중입니다")
            print(f"   응답: {response.json()}")
        else:
            print(f"   서버 응답 오류: {response.status_code}")
            return False
    except requests.exceptions.ConnectionRefusedError:
        print("   서버에 연결할 수 없습니다")
        print(f"   Python API 서버를 시작하세요: python start_python_api.py")
        return False
    except Exception as e:
        print(f"   오류 발생: {e}")
        return False
    
    print("\n2. 종목 목록 확인...")
    try:
        response = requests.get(f"{base_url}/api/symbols", timeout=5)
        if response.status_code == 200:
            symbols = response.json().get('symbols', [])
            print(f"   사용 가능한 종목: {len(symbols)}개")
            print(f"   종목: {', '.join(symbols[:5])}...")
            test_symbol = symbols[0] if symbols else "AAPL"
        else:
            print(f"   종목 목록 조회 실패: {response.status_code}")
            test_symbol = "AAPL"
    except Exception as e:
        print(f"   종목 목록 조회 실패: {e}")
        test_symbol = "AAPL"
    
    print(f"\n3. 실시간 데이터 확인 ({test_symbol})...")
    try:
        response = requests.get(f"{base_url}/api/realtime/{test_symbol}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   실시간 데이터 조회 성공")
            print(f"   - 심볼: {data.get('symbol', 'N/A')}")
            print(f"   - 현재가: ${data.get('currentPrice', data.get('price', 0)):.2f}")
            print(f"   - 변동률: {data.get('changePercent', data.get('change_percent', 0)):.2f}%")
            print(f"   - 거래량: {data.get('volume', 0):,}")
        else:
            print(f"   실시간 데이터 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"   실시간 데이터 조회 실패: {e}")
    
    print(f"\n4. 기술적 분석 데이터 확인 ({test_symbol})...")
    print("   (RSI, MACD 값 확인)")
    try:
        response = requests.get(f"{base_url}/api/analysis/{test_symbol}", timeout=15)
        if response.status_code == 200:
            data = response.json()
            signals = data.get('signals', {})
            
            print("   기술적 분석 데이터 조회 성공")
            print(f"   - 심볼: {data.get('symbol', 'N/A')}")
            print(f"   - 트렌드: {data.get('trend', 'N/A')}")
            print(f"   - 트렌드 강도: {data.get('trendStrength', data.get('trend_strength', 0)):.2f}")
            
            rsi = signals.get('rsi')
            if rsi is not None and rsi != 0:
                print(f"   RSI: {rsi:.2f}")
            else:
                print(f"   RSI: {rsi} (데이터 없음!)")
            
            macd = signals.get('macd')
            if macd is not None and macd != 0:
                print(f"   MACD: {macd:.4f}")
            else:
                print(f"   MACD: {macd} (데이터 없음!)")
            
            macd_signal = signals.get('macdSignal') or signals.get('macd_signal')
            if macd_signal is not None and macd_signal != 0:
                print(f"   MACD Signal: {macd_signal:.4f}")
            else:
                print(f"   MACD Signal: {macd_signal} (데이터 없음)")
            
            print(f"\n   전체 signals 데이터:")
            print(f"   {json.dumps(signals, indent=6, ensure_ascii=False)}")
            
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
            print(f"   기술적 분석 데이터 조회 실패: {response.status_code}")
            print(f"   응답: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   기술적 분석 데이터 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n5. 과거 데이터 확인 ({test_symbol}, 30일)...")
    try:
        response = requests.get(f"{base_url}/api/historical/{test_symbol}?days=30", timeout=10)
        if response.status_code == 200:
            data = response.json()
            chart_data = data.get('data', [])
            print(f"   과거 데이터 조회 성공: {len(chart_data)}개 데이터 포인트")
            if len(chart_data) > 0:
                last_point = chart_data[-1]
                print(f"   - 최근 날짜: {last_point.get('date', 'N/A')}")
                print(f"   - 최근 가격: ${last_point.get('close', 0):.2f}")
                print(f"   - 최근 RSI: {last_point.get('rsi', 'N/A')}")
                print(f"   - 최근 MACD: {last_point.get('macd', 'N/A')}")
        else:
            print(f"   과거 데이터 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"   과거 데이터 조회 실패: {e}")
    
    print("\n" + "=" * 60)
    print("확인 완료!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    success = check_python_api(port)
    sys.exit(0 if success else 1)

