import logging
import traceback
import sys
import time
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Callable, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncio
from functools import wraps
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from collections import defaultdict, deque
import threading
from config.settings import get_settings

settings = get_settings()

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    API = "api"
    DATABASE = "database"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    SYSTEM = "system"

@dataclass
class ErrorContext:
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    client_ip: Optional[str] = None
    endpoint: Optional[str] = None
    parameters: Optional[Dict] = None
    timestamp: datetime = None
    retry_count: int = 0
    recovery_attempted: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class ErrorReport:
    error_id: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception: Optional[Exception]
    context: ErrorContext
    stack_trace: str
    timestamp: datetime
    resolved: bool = False
    resolution_notes: Optional[str] = None
    recovery_strategy: Optional[str] = None
    recovery_attempts: int = 0
    recovery_success: bool = False

@dataclass
class RecoveryStrategy:
    strategy_type: str
    max_attempts: int = 3
    backoff_multiplier: float = 2.0
    base_delay: float = 1.0
    max_delay: float = 60.0
    conditions: Dict = field(default_factory=dict)
    action: Optional[Callable] = None

class ErrorManager:
    
    def __init__(self):
        self.error_reports = []
        self.error_counts = {}
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,
            ErrorSeverity.HIGH: 5,
            ErrorSeverity.MEDIUM: 20,
            ErrorSeverity.LOW: 50
        }
        self.notification_handlers = []
        self.circuit_breakers = {}
        self.retry_strategies = {}
        self.recovery_strategies = {}
        self.error_patterns = defaultdict(int)
        self.recent_errors = deque(maxlen=1000)
        self.lock = threading.Lock()
        self._initialize_recovery_strategies()
        
    def _initialize_recovery_strategies(self):
        self.recovery_strategies = {
            'network_timeout': RecoveryStrategy(
                strategy_type='retry_with_backoff',
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                conditions={'error_type': 'timeout', 'category': ErrorCategory.NETWORK}
            ),
            'database_connection': RecoveryStrategy(
                strategy_type='reconnect',
                max_attempts=5,
                base_delay=2.0,
                max_delay=30.0,
                conditions={'error_type': 'connection', 'category': ErrorCategory.DATABASE}
            ),
            'api_rate_limit': RecoveryStrategy(
                strategy_type='exponential_backoff',
                max_attempts=5,
                base_delay=5.0,
                max_delay=300.0,
                conditions={'error_type': 'rate_limit', 'category': ErrorCategory.API}
            ),
            'data_validation': RecoveryStrategy(
                strategy_type='fallback_data',
                max_attempts=1,
                conditions={'error_type': 'validation', 'category': ErrorCategory.VALIDATION}
            ),
            'external_service': RecoveryStrategy(
                strategy_type='circuit_breaker',
                max_attempts=3,
                base_delay=10.0,
                conditions={'error_type': 'service_unavailable', 'category': ErrorCategory.NETWORK}
            )
        }
        
    def register_notification_handler(self, handler: Callable):
        self.notification_handlers.append(handler)
    
    def log_error(self, 
                  severity: ErrorSeverity,
                  category: ErrorCategory,
                  message: str,
                  exception: Optional[Exception] = None,
                  context: Optional[ErrorContext] = None) -> str:
        
        with self.lock:
            error_id = f"ERR_{int(time.time())}_{hash(message) % 10000}"
            
            if context is None:
                context = ErrorContext()
            
            stack_trace = ""
            error_type = "unknown"
            if exception:
                stack_trace = traceback.format_exc()
                error_type = self._classify_error(exception, message)
            
            error_report = ErrorReport(
                error_id=error_id,
                severity=severity,
                category=category,
                message=message,
                exception=exception,
                context=context,
                stack_trace=stack_trace,
                timestamp=datetime.utcnow()
            )
            
            self.error_reports.append(error_report)
            self.recent_errors.append(error_report)
            self._update_error_counts(severity, category)
            self._update_error_patterns(error_type, category)
            self._check_alert_thresholds(severity, category)
            
            recovery_result = self._attempt_recovery(error_report, error_type)
            if recovery_result:
                error_report.recovery_strategy = recovery_result['strategy']
                error_report.recovery_attempts = recovery_result['attempts']
                error_report.recovery_success = recovery_result['success']
            
            self._log_to_file(error_report)
            
            return error_id
    
    def _classify_error(self, exception: Exception, message: str) -> str:
        error_str = str(exception).lower()
        message_lower = message.lower()
        
        if 'timeout' in error_str or 'timeout' in message_lower:
            return 'timeout'
        elif 'connection' in error_str or 'connection' in message_lower:
            return 'connection'
        elif 'rate limit' in error_str or 'rate limit' in message_lower:
            return 'rate_limit'
        elif 'validation' in error_str or 'validation' in message_lower:
            return 'validation'
        elif 'service unavailable' in error_str or '503' in error_str:
            return 'service_unavailable'
        elif 'not found' in error_str or '404' in error_str:
            return 'not_found'
        elif 'unauthorized' in error_str or '401' in error_str:
            return 'unauthorized'
        elif 'forbidden' in error_str or '403' in error_str:
            return 'forbidden'
        else:
            return 'unknown'
    
    def _update_error_counts(self, severity: ErrorSeverity, category: ErrorCategory):
        key = f"{severity.value}_{category.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def _update_error_patterns(self, error_type: str, category: ErrorCategory):
        pattern_key = f"{error_type}_{category.value}"
        self.error_patterns[pattern_key] += 1
    
    def _check_alert_thresholds(self, severity: ErrorSeverity, category: ErrorCategory):
        key = f"{severity.value}_{category.value}"
        count = self.error_counts.get(key, 0)
        threshold = self.alert_thresholds.get(severity, 100)
        
        if count >= threshold:
            self._send_alert(severity, category, count)
    
    def _send_alert(self, severity: ErrorSeverity, category: ErrorCategory, count: int):
        alert_message = f"Alert: {count} {severity.value} errors in {category.value} category"
        
        for handler in self.notification_handlers:
            try:
                handler(severity, category, alert_message)
            except Exception as e:
                logging.error(f"알림 핸들러 오류: {e}")
    
    def _attempt_recovery(self, error_report: ErrorReport, error_type: str) -> Optional[Dict]:
        for strategy_name, strategy in self.recovery_strategies.items():
            if self._matches_recovery_conditions(strategy, error_type, error_report):
                return self._execute_recovery_strategy(strategy, error_report)
        return None
    
    def _matches_recovery_conditions(self, strategy: RecoveryStrategy, error_type: str, error_report: ErrorReport) -> bool:
        conditions = strategy.conditions
        if 'error_type' in conditions and conditions['error_type'] != error_type:
            return False
        if 'category' in conditions and conditions['category'] != error_report.category:
            return False
        return True
    
    def _execute_recovery_strategy(self, strategy: RecoveryStrategy, error_report: ErrorReport) -> Dict:
        error_report.recovery_attempts += 1
        
        if strategy.strategy_type == 'retry_with_backoff':
            return self._retry_with_backoff(strategy, error_report)
        elif strategy.strategy_type == 'reconnect':
            return self._reconnect_strategy(strategy, error_report)
        elif strategy.strategy_type == 'exponential_backoff':
            return self._exponential_backoff(strategy, error_report)
        elif strategy.strategy_type == 'fallback_data':
            return self._fallback_data_strategy(strategy, error_report)
        elif strategy.strategy_type == 'circuit_breaker':
            return self._circuit_breaker_strategy(strategy, error_report)
        else:
            return {'strategy': strategy.strategy_type, 'attempts': 0, 'success': False}
    
    def _retry_with_backoff(self, strategy: RecoveryStrategy, error_report: ErrorReport) -> Dict:
        attempts = 0
        delay = strategy.base_delay
        
        while attempts < strategy.max_attempts:
            attempts += 1
            try:
                time.sleep(delay)
                if error_report.context.retry_count < strategy.max_attempts:
                    error_report.context.retry_count += 1
                    return {'strategy': 'retry_with_backoff', 'attempts': attempts, 'success': True}
            except Exception as e:
                logging.warning(f"재시도 시도 {attempts} 실패: {e}")
            
            delay = min(delay * strategy.backoff_multiplier, strategy.max_delay)
        
        return {'strategy': 'retry_with_backoff', 'attempts': attempts, 'success': False}
    
    def _reconnect_strategy(self, strategy: RecoveryStrategy, error_report: ErrorReport) -> Dict:
        attempts = 0
        delay = strategy.base_delay
        
        while attempts < strategy.max_attempts:
            attempts += 1
            try:
                time.sleep(delay)
                if error_report.category == ErrorCategory.DATABASE:
                    return {'strategy': 'reconnect', 'attempts': attempts, 'success': True}
            except Exception as e:
                logging.warning(f"재연결 시도 {attempts} 실패: {e}")
            
            delay = min(delay * strategy.backoff_multiplier, strategy.max_delay)
        
        return {'strategy': 'reconnect', 'attempts': attempts, 'success': False}
    
    def _exponential_backoff(self, strategy: RecoveryStrategy, error_report: ErrorReport) -> Dict:
        attempts = 0
        delay = strategy.base_delay
        
        while attempts < strategy.max_attempts:
            attempts += 1
            try:
                time.sleep(delay)
                if error_report.category == ErrorCategory.API:
                    return {'strategy': 'exponential_backoff', 'attempts': attempts, 'success': True}
            except Exception as e:
                logging.warning(f"지수 백오프 시도 {attempts} 실패: {e}")
            
            delay = min(delay * (2 ** attempts), strategy.max_delay)
        
        return {'strategy': 'exponential_backoff', 'attempts': attempts, 'success': False}
    
    def _fallback_data_strategy(self, strategy: RecoveryStrategy, error_report: ErrorReport) -> Dict:
        if error_report.category == ErrorCategory.VALIDATION:
            return {'strategy': 'fallback_data', 'attempts': 1, 'success': True}
        return {'strategy': 'fallback_data', 'attempts': 1, 'success': False}
    
    def _circuit_breaker_strategy(self, strategy: RecoveryStrategy, error_report: ErrorReport) -> Dict:
        service_key = f"{error_report.category.value}_service"
        
        if service_key not in self.circuit_breakers:
            self.circuit_breakers[service_key] = CircuitBreaker(
                failure_threshold=5,
                timeout=60
            )
        
        cb = self.circuit_breakers[service_key]
        
        if cb.state == "OPEN":
            return {'strategy': 'circuit_breaker', 'attempts': 0, 'success': False}
        
        attempts = 0
        while attempts < strategy.max_attempts:
            attempts += 1
            try:
                if cb.state == "CLOSED" or cb.state == "HALF_OPEN":
                    return {'strategy': 'circuit_breaker', 'attempts': attempts, 'success': True}
            except Exception as e:
                logging.warning(f"서킷 브레이커 시도 {attempts} 실패: {e}")
        
        return {'strategy': 'circuit_breaker', 'attempts': attempts, 'success': False}
    
    def _log_to_file(self, error_report: ErrorReport):
        log_entry = {
            'error_id': error_report.error_id,
            'severity': error_report.severity.value,
            'category': error_report.category.value,
            'message': error_report.message,
            'timestamp': error_report.timestamp.isoformat(),
            'context': asdict(error_report.context),
            'stack_trace': error_report.stack_trace,
            'recovery_strategy': error_report.recovery_strategy,
            'recovery_attempts': error_report.recovery_attempts,
            'recovery_success': error_report.recovery_success
        }
        
        logging.error(json.dumps(log_entry, default=str))
    
    def get_error_statistics(self, hours: int = 24) -> Dict:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_reports if e.timestamp >= cutoff_time]
        
        stats = {
            'total_errors': len(recent_errors),
            'by_severity': {},
            'by_category': {},
            'unresolved': len([e for e in recent_errors if not e.resolved]),
            'critical_errors': len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL]),
            'recovery_success_rate': 0.0,
            'error_patterns': dict(self.error_patterns),
            'circuit_breaker_states': {k: cb.state for k, cb in self.circuit_breakers.items()}
        }
        
        for severity in ErrorSeverity:
            stats['by_severity'][severity.value] = len([e for e in recent_errors if e.severity == severity])
        
        for category in ErrorCategory:
            stats['by_category'][category.value] = len([e for e in recent_errors if e.category == category])
        
        recovery_attempts = [e for e in recent_errors if e.recovery_attempts > 0]
        if recovery_attempts:
            successful_recoveries = len([e for e in recovery_attempts if e.recovery_success])
            stats['recovery_success_rate'] = successful_recoveries / len(recovery_attempts)
        
        return stats
    
    def resolve_error(self, error_id: str, resolution_notes: str = ""):
        for error in self.error_reports:
            if error.error_id == error_id:
                error.resolved = True
                error.resolution_notes = resolution_notes
                break
    
    def get_unresolved_errors(self, severity: Optional[ErrorSeverity] = None) -> List[ErrorReport]:
        errors = [e for e in self.error_reports if not e.resolved]
        if severity:
            errors = [e for e in errors if e.severity == severity]
        return errors
    
    def cleanup_old_errors(self, days: int = 30):
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        self.error_reports = [e for e in self.error_reports if e.timestamp >= cutoff_time]

class CircuitBreaker:
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        self.success_count = 0
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        with self.lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                    self.success_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.success_count += 1
                    if self.success_count >= 2:
                        self.state = "CLOSED"
                        self.failure_count = 0
                        self.success_count = 0
                elif self.state == "CLOSED":
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                
                raise e

class RetryStrategy:
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute(self, func: Callable, *args, **kwargs):
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
        
        raise last_exception

def error_handler(severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 category: ErrorCategory = ErrorCategory.SYSTEM,
                 reraise: bool = False):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            error_manager = getattr(wrapper, 'error_manager', None)
            if not error_manager:
                error_manager = ErrorManager()
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext()
                if 'request' in kwargs:
                    req = kwargs['request']
                    context.client_ip = getattr(req.client, 'host', None) if hasattr(req, 'client') else None
                    context.endpoint = str(req.url) if hasattr(req, 'url') else None
                
                error_id = error_manager.log_error(
                    severity=severity,
                    category=category,
                    message=f"Error in {func.__name__}: {str(e)}",
                    exception=e,
                    context=context
                )
                
                if reraise:
                    raise e
                
                return None
        return wrapper
    return decorator

def validate_data_integrity(data: Any, schema: Dict) -> Tuple[bool, List[str]]:
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Data must be a dictionary")
        return False, errors
    
    for field, rules in schema.items():
        if field not in data:
            if rules.get('required', False):
                errors.append(f"Required field '{field}' is missing")
            continue
        
        value = data[field]
        field_type = rules.get('type', str)
        
        if not isinstance(value, field_type):
            errors.append(f"Field '{field}' must be of type {field_type.__name__}")
            continue
        
        if 'min_length' in rules and len(str(value)) < rules['min_length']:
            errors.append(f"Field '{field}' is too short (minimum {rules['min_length']} characters)")
        
        if 'max_length' in rules and len(str(value)) > rules['max_length']:
            errors.append(f"Field '{field}' is too long (maximum {rules['max_length']} characters)")
        
        if 'pattern' in rules and not re.match(rules['pattern'], str(value)):
            errors.append(f"Field '{field}' does not match required pattern")
    
    return len(errors) == 0, errors

class DataValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Data validation failed: {', '.join(errors)}")

class BusinessLogicError(Exception):
    def __init__(self, message: str, error_code: str = None):
        self.error_code = error_code
        super().__init__(message)

class ExternalServiceError(Exception):
    def __init__(self, service_name: str, message: str, status_code: int = None):
        self.service_name = service_name
        self.status_code = status_code
        super().__init__(f"External service '{service_name}' error: {message}")

def send_error_notification(error_report: ErrorReport):
    try:
        if not settings.EMAIL_USER or not settings.EMAIL_PASSWORD:
            return
        
        msg = MimeMultipart()
        msg['From'] = settings.EMAIL_USER
        msg['To'] = settings.EMAIL_USER
        msg['Subject'] = f"Stock Analysis System Error - {error_report.severity.value.upper()}"
        
        body = f"""
        Error ID: {error_report.error_id}
        Severity: {error_report.severity.value}
        Category: {error_report.category.value}
        Message: {error_report.message}
        Timestamp: {error_report.timestamp}
        Recovery Strategy: {error_report.recovery_strategy or 'None'}
        Recovery Success: {error_report.recovery_success}
        
        Stack Trace:
        {error_report.stack_trace}
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        server = smtplib.SMTP(settings.EMAIL_SMTP_SERVER, settings.EMAIL_SMTP_PORT)
        server.starttls()
        server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
    except Exception as e:
        logging.error(f"오류 알림 전송 실패: {e}")

def initialize_error_management():
    error_manager = ErrorManager()
    error_manager.register_notification_handler(send_error_notification)
    return error_manager
