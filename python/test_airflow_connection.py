import sys
from utils.service_checker import ServiceChecker
from utils.print_utils import PrintFormatter

def test_connections():
    PrintFormatter.print_header("Airflow DAG 연결 테스트")
    
    hosts = ['localhost', 'host.docker.internal']
    
    for host in hosts:
        print(f"\n[{host}] 테스트:")
        PrintFormatter.print_status("호스트", True, host)
        
        spring_online, spring_response = ServiceChecker.check_service('spring_boot', host)
        PrintFormatter.print_status(
            "Spring Boot",
            spring_online,
            f"{host}:8080" if spring_online else spring_response.error
        )
        
        python_online, python_response = ServiceChecker.check_service('python_api', host)
        PrintFormatter.print_status(
            "Python API",
            python_online,
            f"{host}:9000" if python_online else python_response.error
        )
    
    print(PrintFormatter.header("권장사항"))
    print("1. 로컬에서 실행 중이라면 BACKEND_HOST=localhost 설정")
    print("2. Docker에서 실행 중이라면 BACKEND_HOST=host.docker.internal 설정")
    print("3. Airflow UI에서 DAG의 태스크 로그 확인")

if __name__ == "__main__":
    test_connections()






