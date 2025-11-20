from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

class DataFormatter:
    @staticmethod
    def format_realtime_response(data: Dict[str, Any], confidence_score: Optional[float] = None) -> Dict[str, Any]:
        if confidence_score is None:
            confidence_score = data.get('confidence_score', 0.95)
        
        return {
            'symbol': data['symbol'],
            'currentPrice': data['price'],
            'volume': data.get('volume', 0),
            'changePercent': data.get('change_percent', 0),
            'timestamp': data.get('timestamp', datetime.now()),
            'confidenceScore': confidence_score
        }
    
    @staticmethod
    def format_fallback_data(fallback_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'symbol': fallback_data['symbol'],
            'currentPrice': fallback_data['price'],
            'volume': fallback_data.get('volume', 0),
            'changePercent': fallback_data.get('change_percent', 0),
            'timestamp': fallback_data.get('timestamp', datetime.now()),
            'confidenceScore': 0.3
        }
    
    @staticmethod
    def safe_get_float(data: Dict, key: str, default: float = 0.0) -> float:
        value = data.get(key)
        if value is None:
            return default
        try:
            return float(value) if not pd.isna(value) else default
        except (ValueError, TypeError):
            return default

