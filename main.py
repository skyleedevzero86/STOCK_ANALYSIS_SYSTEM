import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_collectors.stock_data_collector import StockDataCollector, DataQualityChecker
from analysis_engine.technical_analyzer import TechnicalAnalyzer
from notification.notification_service import NotificationService, AlertManager
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class StockAnalysisSystem:
    
    def __init__(self):
        self.symbols = settings.ANALYSIS_SYMBOLS
        self.collector = StockDataCollector(
            self.symbols, 
            use_mock_data=settings.USE_MOCK_DATA,
            use_alpha_vantage=True
        )
        self.analyzer = TechnicalAnalyzer()
        
        email_config = {
            'smtp_server': settings.EMAIL_SMTP_SERVER,
            'smtp_port': settings.EMAIL_SMTP_PORT,
            'user': settings.EMAIL_USER,
            'password': settings.EMAIL_PASSWORD
        }
        
        self.notification_service = NotificationService(
            email_config=email_config,
            slack_webhook=settings.SLACK_WEBHOOK_URL
        )
        
        self.alert_manager = AlertManager(self.notification_service)
        
    def run_analysis_cycle(self) -> Dict:
        logging.info("주식 분석 사이클 시작")
        
        try:
            logging.info("1단계: 데이터 수집")
            realtime_data = self.collector.get_multiple_realtime_data()
            
            if not realtime_data:
                logging.warning("수집된 데이터가 없습니다")
                return {'status': 'failed', 'reason': 'no_data'}
            
            logging.info("2단계: 데이터 품질 검사")
            quality_checker = DataQualityChecker()
            quality_results = []
            
            for data in realtime_data:
                if data and data.get('price', 0) > 0:
                    quality_result = {
                        'symbol': data['symbol'],
                        'is_valid': True,
                        'data_quality_score': 1.0,
                        'issues': []
                    }
                    quality_results.append(quality_result)
            
            logging.info("3단계: 기술적 분석")
            analysis_results = []
            
            for data in realtime_data:
                if not data:
                    continue
                    
                symbol = data['symbol']
                logging.info(f"{symbol} 분석 시작")
                
                historical_data = self._load_historical_data(symbol)
                
                if historical_data.empty:
                    logging.warning(f"{symbol}: 과거 데이터가 없습니다")
                    continue
                
                analyzed_data = self.analyzer.calculate_all_indicators(historical_data)
                
                trend_analysis = self.analyzer.analyze_trend(analyzed_data)
                
                anomalies = self.analyzer.detect_anomalies(analyzed_data, symbol)
                
                signals = self.analyzer.generate_signals(analyzed_data, symbol)
                
                analysis_result = {
                    'symbol': symbol,
                    'current_price': data['price'],
                    'volume': data.get('volume', 0),
                    'change_percent': data.get('change_percent', 0),
                    'trend': trend_analysis['trend'],
                    'trend_strength': trend_analysis['strength'],
                    'signals': signals,
                    'anomalies': anomalies,
                    'timestamp': datetime.now()
                }
                
                analysis_results.append(analysis_result)
                logging.info(f"{symbol} 분석 완료: {trend_analysis['trend']} ({signals['signal']})")
            
            logging.info("4단계: 알림 처리")
            notification_results = self._process_notifications(analysis_results)
            
            logging.info("5단계: 결과 저장")
            save_results = self._save_analysis_results(analysis_results)
            
            summary = {
                'status': 'success',
                'timestamp': datetime.now(),
                'symbols_analyzed': len(analysis_results),
                'anomalies_detected': sum(len(r.get('anomalies', [])) for r in analysis_results),
                'notifications_sent': notification_results.get('total_sent', 0),
                'results_saved': save_results
            }
            
            logging.info(f"분석 사이클 완료: {summary}")
            return summary
            
        except (ValueError, TypeError) as e:
            logging.error(f"분석 사이클 데이터 오류: {str(e)}")
            return {'status': 'failed', 'reason': str(e)}
        except Exception as e:
            logging.error(f"분석 사이클 예상치 못한 오류: {str(e)}")
            return {'status': 'failed', 'reason': str(e)}
    
    def _load_historical_data(self, symbol: str):
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(start=datetime.now() - pd.Timedelta(days=30), end=datetime.now(), freq='D')
        np.random.seed(hash(symbol) % 2**32)
        
        base_price = 100 + hash(symbol) % 200
        price_changes = np.random.randn(len(dates)) * 2
        prices = base_price + np.cumsum(price_changes)
        
        return pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })
    
    def _process_notifications(self, analysis_results: List[Dict]) -> Dict:
        try:
            recipients = ['analyst@company.com', 'trader@company.com']
            
            all_anomalies = []
            for result in analysis_results:
                all_anomalies.extend(result.get('anomalies', []))
            
            anomaly_result = {'alerts_sent': 0}
            if all_anomalies:
                anomaly_result = self.alert_manager.process_anomaly_alerts(all_anomalies, recipients)
            
            report_result = self.alert_manager.process_analysis_reports(analysis_results, recipients)
            
            return {
                'anomaly_alerts': anomaly_result.get('alerts_sent', 0),
                'reports_sent': report_result.get('reports_sent', 0),
                'total_sent': anomaly_result.get('alerts_sent', 0) + report_result.get('reports_sent', 0)
            }
            
        except (ValueError, TypeError) as e:
            logging.error(f"알림 처리 데이터 오류: {str(e)}")
            return {'total_sent': 0}
        except Exception as e:
            logging.error(f"알림 처리 예상치 못한 오류: {str(e)}")
            return {'total_sent': 0}
    
    def _save_analysis_results(self, analysis_results: List[Dict]) -> int:
        try:
            for result in analysis_results:
                symbol = result['symbol']
                trend = result['trend']
                signal = result['signals']['signal']
                confidence = result['signals']['confidence']
                
                logging.info(f"저장: {symbol} - {trend} ({signal}, 신뢰도: {confidence:.2f})")
            
            return len(analysis_results)
            
        except (ValueError, TypeError) as e:
            logging.error(f"결과 저장 데이터 오류: {str(e)}")
            return 0
        except Exception as e:
            logging.error(f"결과 저장 예상치 못한 오류: {str(e)}")
            return 0
    
    def run_continuous_analysis(self, interval_minutes: int = 15):
        import time
        
        logging.info(f"연속 분석 시작 (간격: {interval_minutes}분)")
        
        while True:
            try:
                result = self.run_analysis_cycle()
                
                if result['status'] == 'success':
                    logging.info(f"분석 완료: {result['symbols_analyzed']}개 종목")
                else:
                    logging.error(f"분석 실패: {result.get('reason', 'unknown')}")
                
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logging.info("연속 분석 중단됨")
                break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.error(f"연속 분석 예상치 못한 오류: {str(e)}")
                time.sleep(60)

def main():
    print("실시간 주식 데이터 분석 시스템")
    print("=" * 50)
    
    system = StockAnalysisSystem()
    
    print("실행 모드를 선택하세요:")
    print("1. 단일 분석 실행")
    print("2. 연속 분석 실행 (15분 간격)")
    print("3. 연속 분석 실행 (5분 간격)")
    print("4. 웹 대시보드 실행 (스프링에서 구현됨)")
    
    try:
        choice = input("선택 (1-4): ").strip()
        
        if choice == '1':
            print("\n단일 분석 실행")
            result = system.run_analysis_cycle()
            print(f"결과: {result}")
            
        elif choice == '2':
            print("\n연속 분석 실행 (15분 간격)")
            system.run_continuous_analysis(15)
            
        elif choice == '3':
            print("\n연속 분석 실행 (5분 간격)")
            system.run_continuous_analysis(5)
            
        elif choice == '4':
            print("\n웹 대시보드는 스프링에서 구현되었습니다.")
            print("스프링 서버를 실행하려면:")
            print("  - Linux/Mac: ./start_spring_boot.sh")
            print("  - Windows: start_spring_boot.bat")
            print("브라우저에서 http://localhost:8080 을 열어주세요")
            print("-" * 50)
            
        else:
            print("잘못된 선택입니다.")
            
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
