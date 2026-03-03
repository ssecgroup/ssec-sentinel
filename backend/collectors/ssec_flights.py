"""Flight Tracking Collector"""
import requests
import random
from typing import List, Dict, Optional
import logging
from datetime import datetime
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class FlightCollector:
    """Collects flight data from multiple sources"""
    
    def __init__(self):
        self.cache = TTLCache(maxsize=10, ttl=300)  # 5 minute cache
        
        # OpenSky Network API (free, no key required for limited access)
        self.opensky_url = "https://opensky-network.org/api/states/all"
        
        # ADS-B Exchange (requires free API key)
        self.adsb_url = "https://adsbexchange.com/api/aircraft/json/"
    
    async def get_flights_near_location(self, lat: float, lon: float, radius_km: float = 100) -> List[Dict]:
        """Get flights near specific coordinates"""
        
        # Try OpenSky first (free, no auth)
        try:
            flights = await self._get_opensky_flights()
            
            # Filter by distance
            nearby = []
            for flight in flights:
                if flight.get("lat") and flight.get("lon"):
                    dist = self._calculate_distance(
                        lat, lon, 
                        flight["lat"], flight["lon"]
                    )
                    if dist <= radius_km:
                        flight["distance_km"] = round(dist, 1)
                        nearby.append(flight)
            
            return sorted(nearby, key=lambda x: x.get("distance_km", 0))
            
        except Exception as e:
            logger.error(f"Error fetching flights: {e}")
            return self._get_mock_flights(lat, lon, radius_km)
    
    async def _get_opensky_flights(self) -> List[Dict]:
        """Fetch flights from OpenSky Network"""
        try:
            response = requests.get(self.opensky_url, timeout=10)
            data = response.json()
            
            flights = []
            states = data.get("states", [])
            
            for state in states[:100]:  # Limit to 100 flights
                flight = {
                    "callsign": state[1].strip() if state[1] else "Unknown",
                    "country": state[2],
                    "lat": state[6],
                    "lon": state[5],
                    "altitude": state[7],
                    "speed": state[9],
                    "heading": state[10],
                    "squawk": state[3],
                    "is_emergency": state[3] in ["7500", "7600", "7700"],
                    "source": "OpenSky"
                }
                
                # Only include flights with valid coordinates
                if flight["lat"] and flight["lon"]:
                    flights.append(flight)
            
            return flights
            
        except Exception as e:
            logger.error(f"OpenSky error: {e}")
            return []
    
    def _get_mock_flights(self, lat: float, lon: float, radius_km: float) -> List[Dict]:
        """Generate mock flight data for testing"""
        flights = []
        
        # Generate random flights around the location
        for i in range(random.randint(3, 8)):
            # Random offset within radius
            lat_offset = (random.random() - 0.5) * (radius_km / 55)  # Approximate degrees
            lon_offset = (random.random() - 0.5) * (radius_km / 55)
            
            # Random squawk code (7500,7600,7700 are emergency)
            squawk = random.choice(["1200", "1200", "1200", "1200", "7500", "7600", "7700"])
            
            flights.append({
                "callsign": random.choice(["DAL", "UAL", "AAL", "JBU", "SWA", "BAW"]) + str(random.randint(100, 999)),
                "country": "USA",
                "lat": lat + lat_offset,
                "lon": lon + lon_offset,
                "altitude": random.randint(25000, 41000),
                "speed": random.randint(400, 550),
                "heading": random.randint(0, 359),
                "squawk": squawk,
                "is_emergency": squawk in ["7500", "7600", "7700"],
                "source": "Mock",
                "distance_km": round(random.uniform(10, radius_km), 1)
            })
        
        return sorted(flights, key=lambda x: x["distance_km"])
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km (Haversine formula)"""
        import math
        
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    async def get_emergency_flights(self) -> List[Dict]:
        """Get all flights with emergency squawk codes"""
        flights = await self._get_opensky_flights()
        return [f for f in flights if f.get("is_emergency")]
    
    def format_for_map(self, flight: Dict) -> Dict:
        """Format flight data for map display"""
        return {
            "id": f"flight-{flight.get('callsign', 'unknown')}-{random.randint(1000, 9999)}",
            "callsign": flight.get("callsign", "Unknown"),
            "lat": flight.get("lat"),
            "lon": flight.get("lon"),
            "altitude": flight.get("altitude"),
            "speed": flight.get("speed"),
            "heading": flight.get("heading"),
            "is_emergency": flight.get("is_emergency", False),
            "color": "#ff4444" if flight.get("is_emergency") else "#4CAF50",
            "source": flight.get("source", "Unknown"),
            "distance_km": flight.get("distance_km")
        }
