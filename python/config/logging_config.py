import logging
import json
import sys
import os
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

def _get_log_level_from_env() -> int:
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    return level_map.get(level_str, logging.INFO)

class StructuredLogger:
    def __init__(self, name: str, log_file: Optional[str] = None, level: Optional[int] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.log_level = level or _get_log_level_from_env()
        self.logger.setLevel(self.log_level)
        self.logger.propagate = False
        
        if not self.logger.handlers:
            self._setup_handlers(log_file)
    
    def _setup_handlers(self, log_file: Optional[str] = None) -> None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(console_handler)
        
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
    
    def _create_log_entry(self, level: str, message: str, **context: Any) -> Dict[str, Any]:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message
        }
        
        if context:
            entry["context"] = self._sanitize_context(context)
        
        return entry
    
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in context.items():
            try:
                json.dumps(value, default=str)
                sanitized[key] = value
            except (TypeError, ValueError):
                sanitized[key] = str(value)
        return sanitized
    
    def info(self, message: str, **context: Any) -> None:
        log_entry = self._create_log_entry("INFO", message, **context)
        self.logger.info(json.dumps(log_entry, ensure_ascii=False, default=str))
    
    def error(self, message: str, exception: Optional[Exception] = None, **context: Any) -> None:
        if exception:
            context["exception_type"] = type(exception).__name__
            context["exception_message"] = str(exception)
            context["traceback"] = traceback.format_exc()
        
        log_entry = self._create_log_entry("ERROR", message, **context)
        self.logger.error(json.dumps(log_entry, ensure_ascii=False, default=str))
    
    def warning(self, message: str, **context: Any) -> None:
        log_entry = self._create_log_entry("WARNING", message, **context)
        self.logger.warning(json.dumps(log_entry, ensure_ascii=False, default=str))
    
    def debug(self, message: str, **context: Any) -> None:
        log_entry = self._create_log_entry("DEBUG", message, **context)
        self.logger.debug(json.dumps(log_entry, ensure_ascii=False, default=str))
    
    def critical(self, message: str, exception: Optional[Exception] = None, **context: Any) -> None:
        if exception:
            context["exception_type"] = type(exception).__name__
            context["exception_message"] = str(exception)
            context["traceback"] = traceback.format_exc()
        
        log_entry = self._create_log_entry("CRITICAL", message, **context)
        self.logger.critical(json.dumps(log_entry, ensure_ascii=False, default=str))
    
    def exception(self, message: str, **context: Any) -> None:
        exc_info = sys.exc_info()
        if exc_info[0] is not None:
            context["exception_type"] = exc_info[0].__name__
            context["exception_message"] = str(exc_info[1])
            context["traceback"] = traceback.format_exc()
        
        log_entry = self._create_log_entry("ERROR", message, **context)
        self.logger.error(json.dumps(log_entry, ensure_ascii=False, default=str), exc_info=exc_info)
    
    def log_performance(self, operation: str, duration_ms: float, **context: Any) -> None:
        context["operation"] = operation
        context["duration_ms"] = duration_ms
        context["metric_type"] = "performance"
        self.info(f"Performance: {operation} completed in {duration_ms:.2f}ms", **context)
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       duration_ms: float, **context: Any) -> None:
        context["http_method"] = method
        context["path"] = path
        context["status_code"] = status_code
        context["duration_ms"] = duration_ms
        context["metric_type"] = "api_request"
        level = "error" if status_code >= 500 else "warning" if status_code >= 400 else "info"
        getattr(self, level)(f"API {method} {path} - {status_code} ({duration_ms:.2f}ms)", **context)
    
    def log_business_event(self, event_type: str, event_data: Dict[str, Any], **context: Any) -> None:
        context["event_type"] = event_type
        context["event_data"] = event_data
        context["metric_type"] = "business_event"
        self.info(f"Business Event: {event_type}", **context)

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        try:
            if isinstance(record.getMessage(), str) and record.getMessage().startswith('{'):
                return record.getMessage()
            
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_entry, ensure_ascii=False, default=str)
        except Exception:
            return super().format(record)

def get_logger(name: str, log_file: Optional[str] = None, level: Optional[int] = None) -> StructuredLogger:
    return StructuredLogger(name, log_file, level)

def setup_logging(log_file: Optional[str] = None, level: Optional[int] = None) -> None:
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    log_level = level or _get_log_level_from_env()
    root_logger.setLevel(log_level)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
