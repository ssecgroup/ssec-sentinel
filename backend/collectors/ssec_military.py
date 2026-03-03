"""Military Bases Data Collector"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class MilitaryBasesCollector:
    """Collects military installation data"""
    
    def __init__(self):
        # US Military Bases worldwide
        self.us_bases = [
            {"name": "Ramstein Air Base", "type": "US Air Force", "lat": 49.4369, "lon": 7.6003, "country": "Germany"},
            {"name": "Camp Bondsteel", "type": "US Army", "lat": 42.3667, "lon": 21.25, "country": "Kosovo"},
            {"name": "Diego Garcia", "type": "US Navy", "lat": -7.3133, "lon": 72.4111, "country": "British Indian Ocean Territory"},
            {"name": "Naval Station Norfolk", "type": "US Navy", "lat": 36.9468, "lon": -76.3175, "country": "USA"},
            {"name": "Camp Humphreys", "type": "US Army", "lat": 36.9667, "lon": 127.0167, "country": "South Korea"},
            {"name": "Kadena Air Base", "type": "US Air Force", "lat": 26.3556, "lon": 127.7675, "country": "Japan"},
            {"name": "Guantanamo Bay", "type": "US Navy", "lat": 19.9, "lon": -75.15, "country": "Cuba"},
            {"name": "RAF Lakenheath", "type": "US Air Force", "lat": 52.4167, "lon": 0.5667, "country": "UK"},
            {"name": "Camp Lemonnier", "type": "US Navy", "lat": 11.55, "lon": 43.15, "country": "Djibouti"},
            {"name": "Al Udeid Air Base", "type": "US Air Force", "lat": 25.117, "lon": 51.317, "country": "Qatar"}
        ]
        
        # NATO installations
        self.nato_bases = [
            {"name": "SHAPE", "type": "NATO HQ", "lat": 50.5, "lon": 3.9833, "country": "Belgium"},
            {"name": "Allied Maritime Command", "type": "NATO", "lat": 51.45, "lon": -0.95, "country": "UK"},
            {"name": "Allied Air Command", "type": "NATO", "lat": 50.9, "lon": 6.4167, "country": "Germany"},
        ]
        
        # Russian bases (approximate locations from open sources)
        self.russian_bases = [
            {"name": "Tartus Naval Base", "type": "Russian Navy", "lat": 34.9167, "lon": 35.8833, "country": "Syria"},
            {"name": "Khmeimim Air Base", "type": "Russian Air Force", "lat": 35.4167, "lon": 35.9333, "country": "Syria"},
        ]
    
    def get_all_bases(self) -> List[Dict]:
        """Get all military bases"""
        all_bases = []
        
        for base in self.us_bases:
            all_bases.append({
                **base,
                "icon": "🇺🇸",
                "color": "#1E3A8A",
                "source": "US Military"
            })
        
        for base in self.nato_bases:
            all_bases.append({
                **base,
                "icon": "🇪🇺",
                "color": "#003399",
                "source": "NATO"
            })
        
        for base in self.russian_bases:
            all_bases.append({
                **base,
                "icon": "🇷🇺",
                "color": "#D52B1E",
                "source": "Russian Federation"
            })
        
        return all_bases
    
    def get_bases_by_country(self, country: str) -> List[Dict]:
        """Get bases in specific country"""
        return [b for b in self.get_all_bases() if b["country"] == country]
    
    def get_bases_near_conflict(self, lat: float, lon: float, radius_km: float = 500) -> List[Dict]:
        """Find military bases near conflict zone"""
        import math
        
        def distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth's radius in km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        nearby = []
        for base in self.get_all_bases():
            dist = distance(lat, lon, base["lat"], base["lon"])
            if dist <= radius_km:
                nearby.append({**base, "distance_km": round(dist, 1)})
        
        return sorted(nearby, key=lambda x: x["distance_km"])
