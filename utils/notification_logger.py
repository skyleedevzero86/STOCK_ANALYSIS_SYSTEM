from typing import Optional
from datetime import datetime
from config.settings import get_settings
from config.logging_config import get_logger

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

logger = get_logger(__name__, "stock_analysis.log")

class NotificationLogger:
    @staticmethod
    def log_notification(
        user_email: str,
        notification_type: str,
        message: str,
        status: str,
        symbol: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        if not PYMYSQL_AVAILABLE:
            return False
        
        try:
            settings = get_settings()
            conn = pymysql.connect(
                host=settings.MYSQL_HOST,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                database=settings.MYSQL_DATABASE,
                port=settings.MYSQL_PORT,
                charset='utf8mb4'
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO notification_logs 
                (user_email, symbol, notification_type, message, status, sent_at, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_email,
                symbol,
                notification_type,
                message,
                status,
                datetime.now(),
                error_message
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"{notification_type} 발송 이력 저장 완료: {user_email} - {status}")
            return True
        except Exception as e:
            logger.error(f"{notification_type} 발송 이력 저장 실패: {str(e)}")
            return False

