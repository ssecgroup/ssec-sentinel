"""VIEWS Conflict Forecast Collector"""
import requests
import pandas as pd
import numpy as np
from typing import List, Dict
import logging
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class VIEWSCollector:
    """Collects conflict forecast data from VIEWS"""
    
    def __init__(self):
        self.base_url = "https://hapi.humdata.org/api/v1/views-forecast"
        self.cache = TTLCache(maxsize=10, ttl=86400)  # 24 hour cache
    
    async def get_forecasts(self, country: str = None) -> List[Dict]:
        """Get conflict fatality forecasts"""
        
        try:
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            forecasts = []
            for item in data:
                if country and item.get("country") != country:
                    continue
                    
                forecasts.append({
                    "id": f"views-{item.get('id')}",
                    "country": item.get("country"),
                    "lat": item.get("latitude"),
                    "lon": item.get("longitude"),
                    "risk_score": item.get("risk_score", 0),
                    "risk_level": self._get_risk_level(item.get("risk_score", 0)),
                    "forecast_month": item.get("month"),
                    "forecast_year": item.get("year"),
                    "description": f"Conflict risk: {item.get('risk_score', 0)}%",
                    "source": "VIEWS"
                })
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error fetching VIEWS data: {e}")
            return []
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to level"""
        if score > 75:
            return "EXTREME"
        elif score > 50:
            return "HIGH"
        elif score > 25:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_risk_color(self, score: float) -> str:
        """Get color for risk score"""
        if score > 75:
            return "#8B0000"  # Dark red
        elif score > 50:
            return "#FF4444"  # Red
        elif score > 25:
            return "#FF8844"  # Orange
        else:
            return "#4CAF50"  # Green
