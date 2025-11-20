from datetime import datetime
from typing import Optional

class PrintFormatter:
    WIDTH = 60
    
    @staticmethod
    def header(title: str) -> str:
        return f"\n{'=' * PrintFormatter.WIDTH}\n{title}\n{'=' * PrintFormatter.WIDTH}"
    
    @staticmethod
    def section(title: str) -> str:
        return f"\n{'-' * PrintFormatter.WIDTH}\n{title}\n{'-' * PrintFormatter.WIDTH}"
    
    @staticmethod
    def divider() -> str:
        return '-' * PrintFormatter.WIDTH
    
    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def status_icon(success: bool) -> str:
        return "✓" if success else "✗"
    
    @staticmethod
    def print_header(title: str):
        print(PrintFormatter.header(title))
        print(f"확인 시간: {PrintFormatter.timestamp()}\n")
    
    @staticmethod
    def print_status(service_name: str, is_online: bool, details: Optional[str] = None):
        icon = PrintFormatter.status_icon(is_online)
        status_text = "실행 중" if is_online else "실행 안 됨"
        print(f"{icon} {service_name}: {status_text}")
        if details:
            print(f"  {details}")
    
    @staticmethod
    def print_error(service_name: str, error: str):
        print(f"✗ {service_name}: {error}")
    
    @staticmethod
    def print_summary(results: dict):
        print(PrintFormatter.header("요약"))
        for service, (is_online, _) in results.items():
            PrintFormatter.print_status(service, is_online)

