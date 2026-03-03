"""HDX Humanitarian Data Collector"""
import requests
from typing import List, Dict, Optional
import logging
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class HDXCollector:
    """Collects humanitarian data from HDX HAPI"""
    
    def __init__(self):
        self.base_url = "https://hapi.humdata.org/api/v1"
        self.cache = TTLCache(maxsize=50, ttl=3600)
    
    async def get_displacement(self, country: Optional[str] = None) -> List[Dict]:
        """Get internally displaced persons data"""
        cache_key = f"displacement_{country}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        params = {}
        if country:
            params["location_code"] = country
        
        try:
            response = requests.get(
                f"{self.base_url}/displacement",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            self.cache[cache_key] = data
            return data
            
        except Exception as e:
            logger.error(f"Error fetching displacement data: {e}")
            return []
    
    async def get_food_security(self, country: Optional[str] = None) -> List[Dict]:
        """Get food security data (IPC phases)"""
        params = {}
        if country:
            params["location_code"] = country
        
        try:
            response = requests.get(
                f"{self.base_url}/food-security",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching food security data: {e}")
            return []
    
    def format_alert(self, displacement_data: Dict) -> Dict:
        """Format displacement data for map display"""
        return {
            "id": f"hdx-{displacement_data.get('id', '')}",
            "title": f"🏕️ Displacement - {displacement_data.get('location_name', 'Unknown')}",
            "type": "Displacement",
            "lat": displacement_data.get("centroid_lat", 0),
            "lon": displacement_data.get("centroid_lon", 0),
            "alertLevel": "ORANGE",
            "description": f"{displacement_data.get('population', 0):,} people displaced",
            "population": displacement_data.get("population", 0),
            "source": "HDX",
            "timestamp": displacement_data.get("population_date", "")
        }
