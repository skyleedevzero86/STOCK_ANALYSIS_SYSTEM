import logging
import traceback
import sys
import time
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Callable, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from functools import wraps
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
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
        
    def register_notification_handler(self, handler: Callable):
        self.notification_handlers.append(handler)
    
    def log_error(self, 
                  severity: ErrorSeverity,
                  category: ErrorCategory,
                  message: str,
                  exception: Optional[Exception] = None,
                  context: Optional[ErrorContext] = None) -> str:
        
        error_id = f"ERR_{int(time.time())}_{hash(message) % 10000}"
        
        if context is None:
            context = ErrorContext()
        
        stack_trace = ""
        if exception:
            stack_trace = traceback.format_exc()
        
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
        self._update_error_counts(severity, category)
        self._check_alert_thresholds(severity, category)
        
        self._log_to_file(error_report)
        
        return error_id
    
    def _update_error_counts(self, severity: ErrorSeverity, category: ErrorCategory):
        key = f"{severity.value}_{category.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
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
                logging.error(f"Error in notification handler: {e}")
    
    def _log_to_file(self, error_report: ErrorReport):
        log_entry = {
            'error_id': error_report.error_id,
            'severity': error_report.severity.value,
            'category': error_report.category.value,
            'message': error_report.message,
            'timestamp': error_report.timestamp.isoformat(),
            'context': asdict(error_report.context),
            'stack_trace': error_report.stack_trace
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
            'critical_errors': len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL])
        }
        
        for severity in ErrorSeverity:
            stats['by_severity'][severity.value] = len([e for e in recent_errors if e.severity == severity])
        
        for category in ErrorCategory:
            stats['by_category'][category.value] = len([e for e in recent_errors if e.category == category])
        
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
    
    def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
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
        logging.error(f"Failed to send error notification: {e}")

def initialize_error_management():
    error_manager = ErrorManager()
    error_manager.register_notification_handler(send_error_notification)
    return error_manager
