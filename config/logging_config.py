import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class StructuredLogger:
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            if log_file:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def _create_log_entry(self, level: str, message: str, **context: Any) -> Dict[str, Any]:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **context
        }
    
    def info(self, message: str, **context: Any) -> None:
        log_entry = self._create_log_entry("INFO", message, **context)
        self.logger.info(json.dumps(log_entry, ensure_ascii=False, default=str))
    
    def error(self, message: str, **context: Any) -> None:
        log_entry = self._create_log_entry("ERROR", message, **context)
        self.logger.error(json.dumps(log_entry, ensure_ascii=False, default=str))
    
    def warning(self, message: str, **context: Any) -> None:
        log_entry = self._create_log_entry("WARNING", message, **context)
        self.logger.warning(json.dumps(log_entry, ensure_ascii=False, default=str))
    
    def debug(self, message: str, **context: Any) -> None:
        log_entry = self._create_log_entry("DEBUG", message, **context)
        self.logger.debug(json.dumps(log_entry, ensure_ascii=False, default=str))
    
    def critical(self, message: str, **context: Any) -> None:
        log_entry = self._create_log_entry("CRITICAL", message, **context)
        self.logger.critical(json.dumps(log_entry, ensure_ascii=False, default=str))

def get_logger(name: str, log_file: Optional[str] = None) -> StructuredLogger:
    return StructuredLogger(name, log_file)

def setup_logging(log_file: Optional[str] = None) -> None:
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
