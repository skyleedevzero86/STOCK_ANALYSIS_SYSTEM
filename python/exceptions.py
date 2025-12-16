from typing import Optional, Dict, Any


class StockAnalysisBaseException(Exception):
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause


class StockDataCollectionError(StockAnalysisBaseException):
    pass


class DataSourceUnavailableError(StockDataCollectionError):
    pass


class InvalidSymbolError(StockDataCollectionError):
    pass


class StockNotFoundError(StockDataCollectionError):
    pass


class DataValidationError(StockAnalysisBaseException):
    
    def __init__(self, message: str, errors: Optional[list] = None, 
                 error_code: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message, error_code=error_code, cause=cause)
        self.errors = errors or []


class StockAnalysisError(StockAnalysisBaseException):
    pass


class IndicatorCalculationError(StockAnalysisError):
    pass


class PatternDetectionError(StockAnalysisError):
    pass


class NetworkError(StockAnalysisBaseException):
    pass


class ConnectionError(NetworkError):
    pass


class TimeoutError(NetworkError):
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None,
                 error_code: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message, error_code=error_code, cause=cause)
        self.timeout_seconds = timeout_seconds


class RateLimitError(NetworkError):
    
    def __init__(self, message: str, retry_after: Optional[int] = None,
                 error_code: Optional[str] = None, cause: Optional[Exception] = None,
                 service_name: Optional[str] = None):
        super().__init__(message, error_code=error_code, cause=cause)
        self.retry_after = retry_after
        self.service_name = service_name


class HTTPError(NetworkError):
    
    def __init__(self, message: str, status_code: Optional[int] = None,
                 error_code: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message, error_code=error_code, cause=cause)
        self.status_code = status_code


class ExternalServiceError(StockAnalysisBaseException):
    
    def __init__(self, message: str, service_name: str, 
                 status_code: Optional[int] = None, error_code: Optional[str] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message, error_code=error_code, cause=cause)
        self.service_name = service_name
        self.status_code = status_code


class AlphaVantageError(ExternalServiceError):
    pass


class YahooFinanceError(ExternalServiceError):
    pass


class DatabaseError(StockAnalysisBaseException):
    pass


class DatabaseConnectionError(DatabaseError):
    pass


class DatabaseQueryError(DatabaseError):
    pass


class AuthenticationError(StockAnalysisBaseException):
    pass


class AuthorizationError(StockAnalysisBaseException):
    pass


class NotificationError(StockAnalysisBaseException):
    pass


class EmailNotificationError(NotificationError):
    pass


class SMSNotificationError(NotificationError):
    pass


class ConfigurationError(StockAnalysisBaseException):
    pass


class MissingConfigurationError(ConfigurationError):
    pass


class BusinessLogicError(StockAnalysisBaseException):
    pass


class WebSocketError(StockAnalysisBaseException):
    pass


class WebSocketConnectionError(WebSocketError):
    pass


class AirflowError(StockAnalysisBaseException):
    pass


class DAGExecutionError(AirflowError):
    pass


class CircuitBreakerOpenError(StockAnalysisBaseException):
    pass
