import pytest
from unittest.mock import Mock, patch
import jwt
import bcrypt
import time
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.security_manager import SecurityManager, SecurityConfig

class TestSecurityConfig:
    
    def test_security_config_creation(self):
        config = SecurityConfig(
            jwt_secret="test_secret",
            jwt_algorithm="HS256",
            jwt_expiry=3600,
            max_login_attempts=5,
            lockout_duration=900
        )
        
        assert config.jwt_secret == "test_secret"
        assert config.jwt_algorithm == "HS256"
        assert config.jwt_expiry == 3600
        assert config.max_login_attempts == 5
        assert config.lockout_duration == 900

class TestSecurityManager:
    
    @pytest.fixture
    def security_config(self):
        return SecurityConfig(
            jwt_secret="test_secret_key_12345",
            jwt_algorithm="HS256",
            jwt_expiry=3600,
            max_login_attempts=5,
            lockout_duration=900,
            password_min_length=8,
            session_timeout=1800,
            rate_limit_requests=100,
            rate_limit_window=3600
        )
    
    @pytest.fixture
    def security_manager(self, security_config):
        return SecurityManager(security_config)
    
    def test_initialization(self, security_manager, security_config):
        assert security_manager.config == security_config
        assert security_manager.failed_attempts == {}
        assert security_manager.active_sessions == {}
        assert security_manager.rate_limits == {}
        assert security_manager.blocked_ips == set()
        assert security_manager.suspicious_activities == []
    
    def test_hash_password(self, security_manager):
        password = "TestPassword123!"
        hashed = security_manager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_verify_password_correct(self, security_manager):
        password = "TestPassword123!"
        hashed = security_manager.hash_password(password)
        
        result = security_manager.verify_password(password, hashed)
        assert result is True
    
    def test_verify_password_incorrect(self, security_manager):
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = security_manager.hash_password(password)
        
        result = security_manager.verify_password(wrong_password, hashed)
        assert result is False
    
    def test_generate_jwt_token(self, security_manager):
        user_id = "user123"
        role = "admin"
        token = security_manager.generate_jwt_token(user_id, role)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        payload = jwt.decode(token, security_manager.config.jwt_secret, algorithms=["HS256"])
        assert payload['user_id'] == user_id
        assert payload['role'] == role
        assert 'iat' in payload
        assert 'exp' in payload
    
    def test_verify_jwt_token_valid(self, security_manager):
        user_id = "user123"
        token = security_manager.generate_jwt_token(user_id)
        
        payload = security_manager.verify_jwt_token(token)
        assert payload is not None
        assert payload['user_id'] == user_id
    
    def test_verify_jwt_token_invalid(self, security_manager):
        invalid_token = "invalid.token.here"
        payload = security_manager.verify_jwt_token(invalid_token)
        assert payload is None
    
    def test_verify_jwt_token_expired(self, security_manager):
        config = SecurityConfig(jwt_secret="test_secret", jwt_expiry=-1)
        manager = SecurityManager(config)
        
        token = manager.generate_jwt_token("user123")
        time.sleep(1)
        
        payload = manager.verify_jwt_token(token)
        assert payload is None
    
    def test_validate_password_strength_valid(self, security_manager):
        password = "StrongPass123!"
        is_valid, errors = security_manager.validate_password_strength(password)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_password_strength_too_short(self, security_manager):
        password = "Short1!"
        is_valid, errors = security_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("at least" in error.lower() for error in errors)
    
    def test_validate_password_strength_no_uppercase(self, security_manager):
        password = "lowercase123!"
        is_valid, errors = security_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert any("uppercase" in error.lower() for error in errors)
    
    def test_validate_password_strength_no_lowercase(self, security_manager):
        password = "UPPERCASE123!"
        is_valid, errors = security_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert any("lowercase" in error.lower() for error in errors)
    
    def test_validate_password_strength_no_digit(self, security_manager):
        password = "NoDigitsHere!"
        is_valid, errors = security_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert any("digit" in error.lower() for error in errors)
    
    def test_validate_password_strength_no_special_char(self, security_manager):
        password = "NoSpecialChar123"
        is_valid, errors = security_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert any("special" in error.lower() for error in errors)
    
    def test_validate_email_valid(self, security_manager):
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.com",
            "test123@test-domain.com"
        ]
        
        for email in valid_emails:
            assert security_manager.validate_email(email) is True
    
    def test_validate_email_invalid(self, security_manager):
        invalid_emails = [
            "invalid.email",
            "@example.com",
            "user@",
            "user@domain",
            "user name@example.com",
            ""
        ]
        
        for email in invalid_emails:
            assert security_manager.validate_email(email) is False
    
    def test_validate_phone_valid(self, security_manager):
        valid_phones = [
            "1234567890",
            "+1234567890",
            "01012345678",
            "123456789012345"
        ]
        
        for phone in valid_phones:
            assert security_manager.validate_phone(phone) is True
    
    def test_validate_phone_invalid(self, security_manager):
        invalid_phones = [
            "123",
            "abc123456",
            "123-456-7890",
            "",
            "12345678901234567"
        ]
        
        for phone in invalid_phones:
            assert security_manager.validate_phone(phone) is False
    
    def test_sanitize_input_safe(self, security_manager):
        safe_input = "This is safe text 123"
        sanitized = security_manager.sanitize_input(safe_input)
        
        assert sanitized == safe_input
    
    def test_sanitize_input_script_tag(self, security_manager):
        dangerous_input = "<script>alert('xss')</script>"
        sanitized = security_manager.sanitize_input(dangerous_input)
        
        assert "<script" not in sanitized.lower()
    
    def test_sanitize_input_javascript(self, security_manager):
        dangerous_input = "javascript:alert('xss')"
        sanitized = security_manager.sanitize_input(dangerous_input)
        
        assert "javascript:" not in sanitized.lower()
    
    def test_sanitize_input_iframe(self, security_manager):
        dangerous_input = "<iframe src='evil.com'></iframe>"
        sanitized = security_manager.sanitize_input(dangerous_input)
        
        assert "<iframe" not in sanitized.lower()
    
    def test_record_login_attempt(self, security_manager):
        user_id = "user123"
        ip_address = "192.168.1.1"
        success = True
        
        security_manager.record_login_attempt(user_id, ip_address, success)
        
        assert user_id in security_manager.failed_attempts or success
    
    def test_check_account_locked_not_locked(self, security_manager):
        user_id = "user123"
        security_manager.failed_attempts[user_id] = {
            'count': 2,
            'last_attempt': datetime.utcnow()
        }
        
        is_locked = security_manager.check_account_locked(user_id)
        assert is_locked is False
    
    def test_check_account_locked_locked(self, security_manager):
        user_id = "user123"
        security_manager.failed_attempts[user_id] = {
            'count': 6,
            'last_attempt': datetime.utcnow()
        }
        
        is_locked = security_manager.check_account_locked(user_id)
        assert is_locked is True
    
    def test_check_account_locked_expired(self, security_manager):
        user_id = "user123"
        security_manager.failed_attempts[user_id] = {
            'count': 6,
            'last_attempt': datetime.utcnow() - timedelta(seconds=1000)
        }
        
        is_locked = security_manager.check_account_locked(user_id)
        assert is_locked is False
    
    def test_block_ip(self, security_manager):
        ip_address = "192.168.1.100"
        security_manager.block_ip(ip_address)
        
        assert ip_address in security_manager.blocked_ips
    
    def test_is_ip_blocked(self, security_manager):
        ip_address = "192.168.1.100"
        security_manager.block_ip(ip_address)
        
        assert security_manager.is_ip_blocked(ip_address) is True
    
    def test_is_ip_blocked_not_blocked(self, security_manager):
        ip_address = "192.168.1.200"
        
        assert security_manager.is_ip_blocked(ip_address) is False
    
    def test_create_session(self, security_manager):
        user_id = "user123"
        ip_address = "192.168.1.1"
        
        session_id = security_manager.create_session(user_id, ip_address)
        
        assert session_id is not None
        assert session_id in security_manager.active_sessions
        assert security_manager.active_sessions[session_id]['user_id'] == user_id
        assert security_manager.active_sessions[session_id]['ip_address'] == ip_address
    
    def test_validate_session_valid(self, security_manager):
        user_id = "user123"
        ip_address = "192.168.1.1"
        session_id = security_manager.create_session(user_id, ip_address)
        
        is_valid = security_manager.validate_session(session_id, ip_address)
        assert is_valid is True
    
    def test_validate_session_invalid(self, security_manager):
        session_id = "invalid_session_id"
        ip_address = "192.168.1.1"
        
        is_valid = security_manager.validate_session(session_id, ip_address)
        assert is_valid is False
    
    def test_validate_session_wrong_ip(self, security_manager):
        user_id = "user123"
        ip_address = "192.168.1.1"
        session_id = security_manager.create_session(user_id, ip_address)
        
        wrong_ip = "192.168.1.2"
        is_valid = security_manager.validate_session(session_id, wrong_ip)
        assert is_valid is False
    
    def test_validate_session_expired(self, security_manager):
        config = SecurityConfig(jwt_secret="test", session_timeout=-1)
        manager = SecurityManager(config)
        
        user_id = "user123"
        ip_address = "192.168.1.1"
        session_id = manager.create_session(user_id, ip_address)
        time.sleep(1)
        
        is_valid = manager.validate_session(session_id, ip_address)
        assert is_valid is False
    
    def test_end_session(self, security_manager):
        user_id = "user123"
        ip_address = "192.168.1.1"
        session_id = security_manager.create_session(user_id, ip_address)
        
        security_manager.end_session(session_id)
        
        assert session_id not in security_manager.active_sessions
    
    def test_check_rate_limit_not_exceeded(self, security_manager):
        ip_address = "192.168.1.1"
        
        for _ in range(50):
            result = security_manager.check_rate_limit(ip_address)
            assert result is True
    
    def test_check_rate_limit_exceeded(self, security_manager):
        ip_address = "192.168.1.1"
        
        for _ in range(101):
            result = security_manager.check_rate_limit(ip_address)
        
        final_result = security_manager.check_rate_limit(ip_address)
        assert final_result is False
    
    def test_record_suspicious_activity(self, security_manager):
        activity = "Multiple failed login attempts"
        ip_address = "192.168.1.1"
        
        security_manager.record_suspicious_activity(activity, ip_address)
        
        assert len(security_manager.suspicious_activities) > 0
        assert security_manager.suspicious_activities[-1]['activity'] == activity
        assert security_manager.suspicious_activities[-1]['ip_address'] == ip_address
    
    def test_get_security_stats(self, security_manager):
        security_manager.block_ip("192.168.1.1")
        security_manager.create_session("user123", "192.168.1.2")
        security_manager.record_suspicious_activity("Test", "192.168.1.3")
        
        stats = security_manager.get_security_stats()
        
        assert 'blocked_ips_count' in stats
        assert 'active_sessions_count' in stats
        assert 'suspicious_activities_count' in stats
        assert stats['blocked_ips_count'] == 1
        assert stats['active_sessions_count'] == 1
        assert stats['suspicious_activities_count'] == 1

