import requests
from typing import Dict, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

class ServiceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class ServiceResponse:
    status: ServiceStatus
    status_code: Optional[int] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    response_time: Optional[float] = None

class HttpClient:
    DEFAULT_TIMEOUT = 5
    
    @staticmethod
    def get(url: str, timeout: float = DEFAULT_TIMEOUT, 
            params: Optional[Dict] = None, 
            auth: Optional[Tuple[str, str]] = None) -> ServiceResponse:
        try:
            import time
            start_time = time.time()
            response = requests.get(url, timeout=timeout, params=params, auth=auth)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except:
                    data = response.text
                return ServiceResponse(
                    status=ServiceStatus.ONLINE,
                    status_code=response.status_code,
                    data=data,
                    response_time=response_time
                )
            else:
                return ServiceResponse(
                    status=ServiceStatus.ERROR,
                    status_code=response.status_code,
                    error=f"HTTP {response.status_code}",
                    response_time=response_time
                )
        except requests.exceptions.Timeout:
            return ServiceResponse(
                status=ServiceStatus.TIMEOUT,
                error="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            return ServiceResponse(
                status=ServiceStatus.OFFLINE,
                error="Connection failed"
            )
        except Exception as e:
            return ServiceResponse(
                status=ServiceStatus.ERROR,
                error=str(e)
            )
    
    @staticmethod
    def post(url: str, timeout: float = DEFAULT_TIMEOUT,
             json_data: Optional[Dict] = None,
             params: Optional[Dict] = None) -> ServiceResponse:
        try:
            import time
            start_time = time.time()
            response = requests.post(url, timeout=timeout, json=json_data, params=params)
            response_time = time.time() - start_time
            
            return ServiceResponse(
                status=ServiceStatus.ONLINE if response.status_code in [200, 201] else ServiceStatus.ERROR,
                status_code=response.status_code,
                data=response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                response_time=response_time
            )
        except requests.exceptions.Timeout:
            return ServiceResponse(status=ServiceStatus.TIMEOUT, error="Request timeout")
        except requests.exceptions.ConnectionError:
            return ServiceResponse(status=ServiceStatus.OFFLINE, error="Connection failed")
        except Exception as e:
            return ServiceResponse(status=ServiceStatus.ERROR, error=str(e))
    
    @staticmethod
    def check_health(base_url: str, health_endpoint: str = "/api/health", 
                    timeout: float = DEFAULT_TIMEOUT) -> ServiceResponse:
        url = f"{base_url.rstrip('/')}{health_endpoint}"
        return HttpClient.get(url, timeout=timeout)

