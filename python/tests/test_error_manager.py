import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from error_handling.error_manager import (
    ErrorManager, ErrorSeverity, ErrorCategory, 
    ErrorContext, ErrorReport
)

class TestErrorSeverity:
    
    def test_error_severity_values(self):
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"

class TestErrorCategory:
    
    def test_error_category_values(self):
        assert ErrorCategory.DATA_COLLECTION.value == "data_collection"
        assert ErrorCategory.ANALYSIS.value == "analysis"
        assert ErrorCategory.API.value == "api"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.SYSTEM.value == "system"

class TestErrorContext:
    
    def test_error_context_creation(self):
        context = ErrorContext(
            user_id="user123",
            session_id="session456",
            request_id="req789",
            client_ip="192.168.1.1",
            endpoint="/api/test",
            parameters={"symbol": "AAPL"}
        )
        
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.request_id == "req789"
        assert context.client_ip == "192.168.1.1"
        assert context.endpoint == "/api/test"
        assert context.parameters == {"symbol": "AAPL"}
        assert context.timestamp is not None
    
    def test_error_context_default_timestamp(self):
        context = ErrorContext()
        assert context.timestamp is not None
        assert isinstance(context.timestamp, datetime)

class TestErrorReport:
    
    def test_error_report_creation(self):
        context = ErrorContext(user_id="user123")
        exception = ValueError("Test error")
        
        report = ErrorReport(
            error_id="ERR_123",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.API,
            message="Test error message",
            exception=exception,
            context=context,
            stack_trace="Traceback...",
            timestamp=datetime.utcnow()
        )
        
        assert report.error_id == "ERR_123"
        assert report.severity == ErrorSeverity.HIGH
        assert report.category == ErrorCategory.API
        assert report.message == "Test error message"
        assert report.exception == exception
        assert report.context == context
        assert report.resolved is False
        assert report.resolution_notes is None

class TestErrorManager:
    
    @pytest.fixture
    def error_manager(self):
        return ErrorManager()
    
    def test_initialization(self, error_manager):
        assert error_manager.error_reports == []
        assert error_manager.error_counts == {}
        assert len(error_manager.alert_thresholds) > 0
        assert error_manager.notification_handlers == []
        assert error_manager.circuit_breakers == {}
        assert error_manager.retry_strategies == {}
    
    def test_log_error(self, error_manager):
        error_id = error_manager.log_error(
            ErrorSeverity.HIGH,
            ErrorCategory.API,
            "Test error message"
        )
        
        assert error_id is not None
        assert len(error_manager.error_reports) == 1
        assert error_manager.error_reports[0].message == "Test error message"
        assert error_manager.error_reports[0].severity == ErrorSeverity.HIGH
        assert error_manager.error_reports[0].category == ErrorCategory.API
    
    def test_log_error_with_exception(self, error_manager):
        exception = ValueError("Test exception")
        error_id = error_manager.log_error(
            ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION,
            "Validation error",
            exception=exception
        )
        
        assert error_id is not None
        assert len(error_manager.error_reports) == 1
        assert error_manager.error_reports[0].exception == exception
        assert len(error_manager.error_reports[0].stack_trace) > 0
    
    def test_log_error_with_context(self, error_manager):
        context = ErrorContext(
            user_id="user123",
            endpoint="/api/test",
            client_ip="192.168.1.1"
        )
        
        error_id = error_manager.log_error(
            ErrorSeverity.LOW,
            ErrorCategory.API,
            "Test error",
            context=context
        )
        
        assert error_id is not None
        assert error_manager.error_reports[0].context == context
    
    def test_get_error_statistics_no_errors(self, error_manager):
        stats = error_manager.get_error_statistics(hours=24)
        
        assert stats['total_errors'] == 0
        assert stats['errors_by_severity'] == {}
        assert stats['errors_by_category'] == {}
    
    def test_get_error_statistics_with_errors(self, error_manager):
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "Error 1")
        error_manager.log_error(ErrorSeverity.MEDIUM, ErrorCategory.ANALYSIS, "Error 2")
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "Error 3")
        
        stats = error_manager.get_error_statistics(hours=24)
        
        assert stats['total_errors'] == 3
        assert stats['errors_by_severity'][ErrorSeverity.HIGH.value] == 2
        assert stats['errors_by_severity'][ErrorSeverity.MEDIUM.value] == 1
        assert stats['errors_by_category'][ErrorCategory.API.value] == 2
        assert stats['errors_by_category'][ErrorCategory.ANALYSIS.value] == 1
    
    def test_get_error_statistics_time_filter(self, error_manager):
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "Recent error")
        
        old_report = error_manager.error_reports[0]
        old_report.timestamp = datetime.utcnow() - timedelta(hours=25)
        
        stats = error_manager.get_error_statistics(hours=24)
        
        assert stats['total_errors'] == 0
    
    def test_get_error_by_id_found(self, error_manager):
        error_id = error_manager.log_error(
            ErrorSeverity.HIGH,
            ErrorCategory.API,
            "Test error"
        )
        
        report = error_manager.get_error_by_id(error_id)
        assert report is not None
        assert report.error_id == error_id
        assert report.message == "Test error"
    
    def test_get_error_by_id_not_found(self, error_manager):
        report = error_manager.get_error_by_id("NONEXISTENT")
        assert report is None
    
    def test_mark_error_resolved(self, error_manager):
        error_id = error_manager.log_error(
            ErrorSeverity.HIGH,
            ErrorCategory.API,
            "Test error"
        )
        
        error_manager.mark_error_resolved(error_id, "Fixed the issue")
        
        report = error_manager.get_error_by_id(error_id)
        assert report.resolved is True
        assert report.resolution_notes == "Fixed the issue"
    
    def test_get_unresolved_errors(self, error_manager):
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "Error 1")
        error_manager.log_error(ErrorSeverity.MEDIUM, ErrorCategory.ANALYSIS, "Error 2")
        
        error_id = error_manager.log_error(ErrorSeverity.LOW, ErrorCategory.VALIDATION, "Error 3")
        error_manager.mark_error_resolved(error_id, "Fixed")
        
        unresolved = error_manager.get_unresolved_errors()
        
        assert len(unresolved) == 2
        assert all(not report.resolved for report in unresolved)
    
    def test_get_errors_by_severity(self, error_manager):
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "High error 1")
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.ANALYSIS, "High error 2")
        error_manager.log_error(ErrorSeverity.MEDIUM, ErrorCategory.API, "Medium error")
        
        high_errors = error_manager.get_errors_by_severity(ErrorSeverity.HIGH)
        
        assert len(high_errors) == 2
        assert all(report.severity == ErrorSeverity.HIGH for report in high_errors)
    
    def test_get_errors_by_category(self, error_manager):
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "API error 1")
        error_manager.log_error(ErrorSeverity.MEDIUM, ErrorCategory.API, "API error 2")
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.ANALYSIS, "Analysis error")
        
        api_errors = error_manager.get_errors_by_category(ErrorCategory.API)
        
        assert len(api_errors) == 2
        assert all(report.category == ErrorCategory.API for report in api_errors)
    
    def test_register_notification_handler(self, error_manager):
        handler = Mock()
        error_manager.register_notification_handler(handler)
        
        assert handler in error_manager.notification_handlers
    
    def test_clear_old_errors(self, error_manager):
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "Recent error")
        
        old_report = error_manager.error_reports[0]
        old_report.timestamp = datetime.utcnow() - timedelta(days=31)
        
        error_manager.clear_old_errors(days=30)
        
        assert len(error_manager.error_reports) == 0
    
    def test_clear_old_errors_keep_recent(self, error_manager):
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "Recent error")
        error_manager.log_error(ErrorSeverity.MEDIUM, ErrorCategory.ANALYSIS, "Old error")
        
        old_report = error_manager.error_reports[1]
        old_report.timestamp = datetime.utcnow() - timedelta(days=31)
        
        error_manager.clear_old_errors(days=30)
        
        assert len(error_manager.error_reports) == 1
        assert error_manager.error_reports[0].message == "Recent error"
    
    def test_get_error_trend(self, error_manager):
        base_time = datetime.utcnow()
        
        for i in range(5):
            error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, f"Error {i}")
            error_manager.error_reports[i].timestamp = base_time - timedelta(hours=i)
        
        trend = error_manager.get_error_trend(hours=24)
        
        assert 'error_count' in trend
        assert 'trend' in trend
        assert trend['error_count'] == 5
    
    def test_get_critical_errors(self, error_manager):
        error_manager.log_error(ErrorSeverity.CRITICAL, ErrorCategory.SYSTEM, "Critical 1")
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "High error")
        error_manager.log_error(ErrorSeverity.CRITICAL, ErrorCategory.DATABASE, "Critical 2")
        
        critical = error_manager.get_critical_errors()
        
        assert len(critical) == 2
        assert all(report.severity == ErrorSeverity.CRITICAL for report in critical)
    
    def test_error_count_by_severity(self, error_manager):
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "High 1")
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.ANALYSIS, "High 2")
        error_manager.log_error(ErrorSeverity.MEDIUM, ErrorCategory.API, "Medium")
        error_manager.log_error(ErrorSeverity.LOW, ErrorCategory.VALIDATION, "Low")
        
        counts = error_manager.get_error_count_by_severity()
        
        assert counts[ErrorSeverity.HIGH] == 2
        assert counts[ErrorSeverity.MEDIUM] == 1
        assert counts[ErrorSeverity.LOW] == 1
        assert counts.get(ErrorSeverity.CRITICAL, 0) == 0
    
    def test_error_count_by_category(self, error_manager):
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, "API 1")
        error_manager.log_error(ErrorSeverity.MEDIUM, ErrorCategory.API, "API 2")
        error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.ANALYSIS, "Analysis")
        error_manager.log_error(ErrorSeverity.LOW, ErrorCategory.DATABASE, "Database")
        
        counts = error_manager.get_error_count_by_category()
        
        assert counts[ErrorCategory.API] == 2
        assert counts[ErrorCategory.ANALYSIS] == 1
        assert counts[ErrorCategory.DATABASE] == 1
    
    def test_get_recent_errors(self, error_manager):
        for i in range(10):
            error_manager.log_error(ErrorSeverity.HIGH, ErrorCategory.API, f"Error {i}")
        
        recent = error_manager.get_recent_errors(limit=5)
        
        assert len(recent) == 5
        assert recent[0].message == "Error 9"
        assert recent[-1].message == "Error 5"

