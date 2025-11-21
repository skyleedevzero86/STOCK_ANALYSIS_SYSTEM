import hashlib
import hmac
import secrets
import jwt
import bcrypt
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from functools import wraps
import ipaddress
import re
from config.settings import settings

@dataclass
class SecurityConfig:
    jwt_secret: str
    jwt_algorithm: str = 'HS256'
    jwt_expiry: int = 3600
    max_login_attempts: int = 5
    lockout_duration: int = 900
    password_min_length: int = 8
    session_timeout: int = 1800
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600

class SecurityManager:
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.failed_attempts = {}
        self.active_sessions = {}
        self.rate_limits = {}
        self.blocked_ips = set()
        self.suspicious_activities = []
        
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_jwt_token(self, user_id: str, role: str = 'user') -> str:
        payload = {
            'user_id': user_id,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=self.config.jwt_expiry)
        }
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        errors = []
        
        if len(password) < self.config.password_min_length:
            errors.append(f"Password must be at least {self.config.password_min_length} characters")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def validate_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone: str) -> bool:
        pattern = r'^\+?1?\d{9,15}$'
        return re.match(pattern, phone) is not None
    
    def sanitize_input(self, input_str: str) -> str:
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe.*?>',
            r'<object.*?>',
            r'<embed.*?>',
            r'<link.*?>',
            r'<meta.*?>',
            r'<style.*?>.*?</style>'
        ]
        
        for pattern in dangerous_patterns:
            input_str = re.sub(pattern, '', input_str, flags=re.IGNORECASE)
        
        return input_str.strip()
    
    def check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        key = f"{client_ip}:{endpoint}"
        current_time = time.time()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = {'requests': [], 'window_start': current_time}
        
        rate_data = self.rate_limits[key]
        
        if current_time - rate_data['window_start'] > self.config.rate_limit_window:
            rate_data['requests'] = []
            rate_data['window_start'] = current_time
        
        rate_data['requests'].append(current_time)
        
        recent_requests = [req_time for req_time in rate_data['requests'] 
                          if current_time - req_time < self.config.rate_limit_window]
        rate_data['requests'] = recent_requests
        
        return len(recent_requests) <= self.config.rate_limit_requests
    
    def check_login_attempts(self, client_ip: str) -> Tuple[bool, int]:
        current_time = time.time()
        
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = {'count': 0, 'last_attempt': 0}
        
        attempt_data = self.failed_attempts[client_ip]
        
        if current_time - attempt_data['last_attempt'] > self.config.lockout_duration:
            attempt_data['count'] = 0
        
        return attempt_data['count'] < self.config.max_login_attempts, attempt_data['count']
    
    def record_failed_login(self, client_ip: str):
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = {'count': 0, 'last_attempt': 0}
        
        self.failed_attempts[client_ip]['count'] += 1
        self.failed_attempts[client_ip]['last_attempt'] = time.time()
        
        if self.failed_attempts[client_ip]['count'] >= self.config.max_login_attempts:
            self.blocked_ips.add(client_ip)
            self._log_suspicious_activity('multiple_failed_logins', client_ip)
    
    def reset_login_attempts(self, client_ip: str):
        if client_ip in self.failed_attempts:
            self.failed_attempts[client_ip]['count'] = 0
    
    def is_ip_blocked(self, client_ip: str) -> bool:
        return client_ip in self.blocked_ips
    
    def validate_ip_address(self, ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def check_geolocation_anomaly(self, client_ip: str, user_location: str) -> bool:
        try:
            import requests
            response = requests.get(f"http://ip-api.com/json/{client_ip}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                country = data.get('country', '')
                return country != user_location
        except:
            pass
        return False
    
    def detect_sql_injection(self, query: str) -> bool:
        sql_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(\b(OR|AND)\b.*\b(1=1|2=2|TRUE|FALSE)\b)',
            r'(\b(OR|AND)\b.*\b(.*=.*)\b)',
            r'(\b(UNION|UNION ALL)\b.*\bSELECT\b)',
            r'(\b(DROP|DELETE|INSERT|UPDATE)\b.*\b(TABLE|DATABASE|INDEX)\b)',
            r'(\b(EXEC|EXECUTE)\b)',
            r'(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)',
            r'(\b(WAITFOR|DELAY)\b)',
            r'(\b(BULK|OPENROWSET|OPENDATASOURCE)\b)',
            r'(\b(SP_|XP_)\b)'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def detect_xss_attack(self, input_str: str) -> bool:
        xss_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe.*?>',
            r'<object.*?>',
            r'<embed.*?>',
            r'<link.*?>',
            r'<meta.*?>',
            r'<style.*?>.*?</style>',
            r'<img.*?src.*?=.*?javascript:',
            r'<a.*?href.*?=.*?javascript:',
            r'<form.*?>',
            r'<input.*?>',
            r'<textarea.*?>',
            r'<select.*?>'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        return False
    
    def generate_csrf_token(self) -> str:
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, token: str, session_token: str) -> bool:
        return hmac.compare_digest(token, session_token)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        key = self.config.jwt_secret.encode('utf-8')
        return hashlib.pbkdf2_hmac('sha256', data.encode('utf-8'), key, 100000).hex()
    
    def create_session(self, user_id: str, client_ip: str) -> str:
        session_id = secrets.token_urlsafe(32)
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'client_ip': client_ip,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        return session_id
    
    def validate_session(self, session_id: str, client_ip: str) -> bool:
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        if session['client_ip'] != client_ip:
            self._log_suspicious_activity('session_ip_mismatch', client_ip)
            return False
        
        if (datetime.utcnow() - session['last_activity']).seconds > self.config.session_timeout:
            del self.active_sessions[session_id]
            return False
        
        session['last_activity'] = datetime.utcnow()
        return True
    
    def invalidate_session(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def _log_suspicious_activity(self, activity_type: str, client_ip: str, details: str = ""):
        activity = {
            'type': activity_type,
            'client_ip': client_ip,
            'timestamp': datetime.utcnow(),
            'details': details
        }
        self.suspicious_activities.append(activity)
        logging.warning(f"Suspicious activity detected: {activity}")
    
    def get_security_report(self) -> Dict:
        return {
            'blocked_ips': len(self.blocked_ips),
            'active_sessions': len(self.active_sessions),
            'failed_attempts': len(self.failed_attempts),
            'suspicious_activities': len(self.suspicious_activities),
            'rate_limited_ips': len(self.rate_limits)
        }
    
    def cleanup_expired_data(self):
        current_time = time.time()
        
        for ip, data in list(self.failed_attempts.items()):
            if current_time - data['last_attempt'] > self.config.lockout_duration * 2:
                del self.failed_attempts[ip]
        
        for session_id, session in list(self.active_sessions.items()):
            if (datetime.utcnow() - session['last_activity']).seconds > self.config.session_timeout * 2:
                del self.active_sessions[session_id]
        
        for key, data in list(self.rate_limits.items()):
            if current_time - data['window_start'] > self.config.rate_limit_window * 2:
                del self.rate_limits[key]

def security_required(required_role: str = 'user'):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                raise ValueError("Request object not found")
            
            client_ip = request.client.host
            security_manager = getattr(request.app.state, 'security_manager', None)
            
            if not security_manager:
                raise ValueError("Security manager not initialized")
            
            if security_manager.is_ip_blocked(client_ip):
                raise ValueError("IP address blocked")
            
            if not security_manager.check_rate_limit(client_ip, func.__name__):
                raise ValueError("Rate limit exceeded")
            
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                raise ValueError("Authentication token required")
            
            payload = security_manager.verify_jwt_token(token)
            if not payload:
                raise ValueError("Invalid or expired token")
            
            if payload.get('role') != required_role and required_role != 'user':
                raise ValueError("Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_input_data(data: Dict) -> Tuple[bool, List[str]]:
    errors = []
    
    for key, value in data.items():
        if isinstance(value, str):
            if len(value) > 1000:
                errors.append(f"Field {key} exceeds maximum length")
            
            if any(char in value for char in ['<', '>', '"', "'", '&']):
                errors.append(f"Field {key} contains potentially dangerous characters")
    
    return len(errors) == 0, errors
