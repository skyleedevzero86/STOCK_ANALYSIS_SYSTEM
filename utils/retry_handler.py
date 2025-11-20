import asyncio
from typing import Callable, TypeVar, Optional, Dict, Any
from functools import wraps
from error_handling.error_manager import ErrorManager, ErrorSeverity, ErrorCategory, ErrorContext
from exceptions import StockAnalysisBaseException
import logging

T = TypeVar('T')

class RetryHandler:
    @staticmethod
    async def execute_with_retry(
        func: Callable,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        error_manager: Optional[ErrorManager] = None,
        context: Optional[ErrorContext] = None,
        *args,
        **kwargs
    ) -> T:
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if context:
                    context.retry_count = attempt
                
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries - 1:
                    delay = retry_delay * (attempt + 1)
                    await asyncio.sleep(delay)
                    continue
                
                if error_manager and context:
                    error_manager.log_error(
                        ErrorSeverity.HIGH,
                        ErrorCategory.DATA_COLLECTION,
                        f"Operation failed after {max_retries} attempts: {str(e)}",
                        e,
                        context
                    )
                
                raise last_exception
        
        raise last_exception
    
    @staticmethod
    def create_error_response(
        error: Exception,
        error_manager: Optional[ErrorManager],
        context: Optional[ErrorContext],
        severity: ErrorSeverity,
        category: ErrorCategory,
        message: str,
        http_status: int = 500
    ) -> tuple[str, int]:
        error_id = ""
        if error_manager:
            error_id = error_manager.log_error(severity, category, message, error, context)
        
        detail = f"{message}. 오류 ID: {error_id}" if error_id else message
        return detail, http_status


