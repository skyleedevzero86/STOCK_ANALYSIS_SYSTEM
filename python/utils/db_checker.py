from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from config.settings import get_settings

try:
    import pymysql
    import pymysql.cursors
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

class DatabaseChecker:
    @staticmethod
    def get_connection():
        if not PYMYSQL_AVAILABLE:
            raise ImportError("pymysql is not available")
        
        settings = get_settings()
        return pymysql.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            port=settings.MYSQL_PORT,
            charset='utf8mb4'
        )
    
    @staticmethod
    def check_subscriptions() -> Tuple[int, List[Dict]]:
        if not PYMYSQL_AVAILABLE:
            return 0, []
        
        try:
            conn = DatabaseChecker.get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            cursor.execute("""
                SELECT id, name, email, is_email_consent, is_phone_consent, 
                       is_active, created_at
                FROM email_subscriptions
                ORDER BY created_at DESC
            """)
            
            subscribers = cursor.fetchall()
            email_consent_count = sum(
                1 for sub in subscribers 
                if sub.get('is_email_consent') and sub.get('is_active')
            )
            
            cursor.close()
            conn.close()
            
            return email_consent_count, subscribers
        except Exception:
            return 0, []
    
    @staticmethod
    def check_notification_logs(hours: int = 24) -> Tuple[int, int, int, List[Dict]]:
        if not PYMYSQL_AVAILABLE:
            return 0, 0, 0, []
        
        try:
            conn = DatabaseChecker.get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT id, user_email, symbol, notification_type, status, 
                       sent_at, error_message
                FROM notification_logs
                WHERE sent_at >= %s
                ORDER BY sent_at DESC
                LIMIT 50
            """, (cutoff_time,))
            
            logs = cursor.fetchall()
            
            sent_count = sum(1 for log in logs if log.get('status') == 'sent')
            failed_count = sum(1 for log in logs if log.get('status') == 'failed')
            pending_count = sum(1 for log in logs if log.get('status') == 'pending')
            
            cursor.close()
            conn.close()
            
            return sent_count, failed_count, pending_count, logs
        except Exception:
            return 0, 0, 0, []

