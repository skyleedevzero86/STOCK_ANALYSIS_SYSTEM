from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .http_client import HttpClient, ServiceResponse, ServiceStatus
from config.settings import get_settings

@dataclass
class ServiceConfig:
    name: str
    base_url: str
    health_endpoint: str
    port: int
    description: str

class ServiceChecker:
    SERVICES = {
        'spring_boot': ServiceConfig(
            name='Spring Boot',
            base_url='http://localhost:8080',
            health_endpoint='/api/email-subscriptions/email-consent',
            port=8080,
            description='Spring Boot 백엔드'
        ),
        'python_api': ServiceConfig(
            name='Python API',
            base_url='http://localhost:9000',
            health_endpoint='/api/health',
            port=9000,
            description='Python API 서버'
        ),
        'airflow': ServiceConfig(
            name='Airflow',
            base_url='http://localhost:8081',
            health_endpoint='/api/v1/dags',
            port=8081,
            description='Airflow 웹서버'
        )
    }
    
    @staticmethod
    def check_service(service_key: str, host: str = 'localhost') -> Tuple[bool, ServiceResponse]:
        if service_key not in ServiceChecker.SERVICES:
            return False, ServiceResponse(status=ServiceStatus.ERROR, error="Unknown service")
        
        config = ServiceChecker.SERVICES[service_key]
        base_url = config.base_url.replace('localhost', host)
        response = HttpClient.check_health(base_url, config.health_endpoint)
        is_online = response.status == ServiceStatus.ONLINE
        return is_online, response
    
    @staticmethod
    def check_all_services(host: str = 'localhost') -> Dict[str, Tuple[bool, ServiceResponse]]:
        results = {}
        for key in ServiceChecker.SERVICES.keys():
            results[key] = ServiceChecker.check_service(key, host)
        return results
    
    @staticmethod
    def check_spring_boot_subscribers(host: str = 'localhost') -> Tuple[int, List[Dict]]:
        config = ServiceChecker.SERVICES['spring_boot']
        url = f"{config.base_url.replace('localhost', host)}{config.health_endpoint}"
        response = HttpClient.get(url)
        
        if response.status == ServiceStatus.ONLINE and response.data:
            data = response.data
            if isinstance(data, dict) and data.get('success'):
                subscriptions = data.get('data', {}).get('subscriptions', [])
                return len(subscriptions), subscriptions
        return 0, []
    
    @staticmethod
    def check_airflow_dag(dag_id: str = 'email_notification_dag', host: str = 'localhost') -> Tuple[bool, Optional[Dict]]:
        config = ServiceChecker.SERVICES['airflow']
        base_url = config.base_url.replace('localhost', host)
        dag_url = f"{base_url}/api/v1/dags/{dag_id}"
        
        response = HttpClient.get(dag_url)
        if response.status == ServiceStatus.ONLINE and response.data:
            dag_data = response.data if isinstance(response.data, dict) else {}
            
            runs_url = f"{dag_url}/dagRuns"
            runs_response = HttpClient.get(runs_url, params={"limit": 5})
            
            runs_data = runs_response.data if runs_response.status == ServiceStatus.ONLINE else {}
            dag_runs = runs_data.get('dag_runs', []) if isinstance(runs_data, dict) else []
            
            return True, {
                'dag_exists': True,
                'runs': dag_runs
            }
        return False, None
    
    @staticmethod
    def check_email_config() -> Tuple[bool, Dict[str, str]]:
        settings = get_settings()
        config = {
            'smtp_server': settings.EMAIL_SMTP_SERVER,
            'smtp_port': str(settings.EMAIL_SMTP_PORT),
            'user': settings.EMAIL_USER,
            'password': '***' if settings.EMAIL_PASSWORD else 'Not set'
        }
        is_valid = all([
            settings.EMAIL_SMTP_SERVER,
            settings.EMAIL_USER,
            settings.EMAIL_PASSWORD
        ])
        return is_valid, config


