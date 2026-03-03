"""HDX Signals - Automated Crisis Alerts"""
import requests
from datetime import datetime
from typing import List, Dict
import logging
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class HDXSignalsCollector:
    """Collects automated crisis alerts from HDX Signals"""
    
    def __init__(self):
        self.base_url = "https://hapi.humdata.org/api/v1/signals"
        self.cache = TTLCache(maxsize=20, ttl=300)  # 5 minute cache
    
    async def get_signals(self, severity: str = None) -> List[Dict]:
        """Get active crisis signals"""
        
        try:
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            signals = response.json()
            
            formatted_signals = []
            for signal in signals:
                if severity and signal.get("severity") != severity:
                    continue
                
                # Parse location if available
                location = signal.get("location", {})
                
                formatted_signals.append({
                    "id": f"signal-{signal.get('id')}",
                    "headline": signal.get("headline", ""),
                    "summary": signal.get("summary", ""),
                    "severity": signal.get("severity", "medium"),
                    "lat": location.get("latitude"),
                    "lon": location.get("longitude"),
                    "country": location.get("country"),
                    "timestamp": signal.get("published_date"),
                    "trend": signal.get("trend_comparison", ""),
                    "topics": signal.get("topics", []),
                    "source": "HDX Signals",
                    "color": self._get_severity_color(signal.get("severity", "medium"))
                })
            
            return formatted_signals
            
        except Exception as e:
            logger.error(f"Error fetching HDX Signals: {e}")
            return []
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level"""
        colors = {
            "high": "#FF4444",
            "medium": "#FF8844",
            "low": "#4CAF50"
        }
        return colors.get(severity, "#FF8844")
    
    async def check_for_new_alerts(self, last_check: datetime) -> List[Dict]:
        """Check for alerts since last check"""
        signals = await self.get_signals()
        
        new_alerts = []
        for signal in signals:
            signal_time = datetime.fromisoformat(signal["timestamp"].replace("Z", "+00:00"))
            if signal_time > last_check:
                new_alerts.append(signal)
        
        return new_alerts
