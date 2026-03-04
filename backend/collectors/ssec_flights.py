"""Flight Tracking Collector - Fixed Version with Retry Logic"""
import requests
import random
import asyncio
import aiohttp
from typing import List, Dict, Optional
import logging
from datetime import datetime
from cachetools import TTLCache
import math
import time

logger = logging.getLogger(__name__)

class FlightCollector:
    """Collects flight data from multiple sources with fallback and retry logic"""
    
    def __init__(self):
        self.cache = TTLCache(maxsize=20, ttl=300)  # 5 minute cache
        
        # OpenSky Network API (free, no key required for limited access)
        self.opensky_url = "https://opensky-network.org/api/states/all"
        
        # ADS-B Exchange (requires free API key - optional)
        self.adsb_url = "https://adsbexchange.com/api/aircraft/json/"
        self.adsb_key = None  # Set if you have a key
        
        # Request settings
        self.timeout = 15  # seconds
        self.max_retries = 3
        self.retry_delay = 2  # seconds base delay
    
    async def get_flights_near_location(self, lat: float, lon: float, radius_km: float = 100) -> List[Dict]:
        """Get flights near specific coordinates with retry logic and fallback"""
        
        # Generate cache key based on approximate grid cell (to avoid too many cache entries)
        cache_key = f"{round(lat/5)},{round(lon/5)},{radius_km}"
        
        # Check cache first
        if cache_key in self.cache:
            logger.info(f"Returning cached flights for {cache_key}")
            return self.cache[cache_key]
        
        logger.info(f"Fetching flights near {lat:.2f}, {lon:.2f} within {radius_km}km")
        
        # Try primary source (OpenSky) with retries
        flights = await self._get_opensky_flights_with_retry()
        
        if flights:
            # Filter by distance
            nearby = self._filter_by_distance(flights, lat, lon, radius_km)
            
            if nearby:
                logger.info(f"Found {len(nearby)} flights near location")
                # Cache the filtered results (not all flights)
                self.cache[cache_key] = nearby
                return nearby
        
        # If OpenSky fails or returns no flights near location, try secondary source
        logger.info("OpenSky failed or returned no nearby flights, trying ADS-B Exchange")
        flights = await self._get_adsb_flights()
        
        if flights:
            nearby = self._filter_by_distance(flights, lat, lon, radius_km)
            if nearby:
                logger.info(f"Found {len(nearby)} flights from ADS-B Exchange")
                self.cache[cache_key] = nearby
                return nearby
        
        # All sources failed - return enhanced mock data
        logger.warning("All flight sources failed, using mock data")
        mock_flights = self._get_mock_flights(lat, lon, radius_km)
        self.cache[cache_key] = mock_flights
        return mock_flights
    
    async def _get_opensky_flights_with_retry(self) -> List[Dict]:
        """Fetch flights from OpenSky Network with exponential backoff retry"""
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"OpenSky attempt {attempt + 1}/{self.max_retries}")
                
                # Use aiohttp for async HTTP with timeout
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(self.opensky_url) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            flights = self._parse_opensky_data(data)
                            logger.info(f"✅ OpenSky success: {len(flights)} flights found")
                            return flights
                        
                        elif response.status == 429:
                            logger.warning(f"OpenSky rate limited (attempt {attempt + 1})")
                            # Rate limited - wait longer
                            wait_time = self.retry_delay * (2 ** attempt) * 2
                            
                        else:
                            logger.warning(f"OpenSky returned status {response.status} (attempt {attempt + 1})")
                            wait_time = self.retry_delay * (2 ** attempt)
                
            except asyncio.TimeoutError:
                logger.warning(f"OpenSky timeout (attempt {attempt + 1})")
                wait_time = self.retry_delay * (2 ** attempt)
                
            except aiohttp.ClientConnectorError as e:
                logger.warning(f"OpenSky connection error (attempt {attempt + 1}): {e}")
                wait_time = self.retry_delay * (2 ** attempt)
                
            except Exception as e:
                logger.warning(f"OpenSky unexpected error (attempt {attempt + 1}): {e}")
                wait_time = self.retry_delay * (2 ** attempt)
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        logger.error("All OpenSky attempts failed")
        return []
    
    def _parse_opensky_data(self, data: Dict) -> List[Dict]:
        """Parse OpenSky API response into standardized flight objects"""
        flights = []
        states = data.get("states", [])
        
        for state in states[:100]:  # Limit to 100 flights to avoid overwhelming
            try:
                # OpenSky state array indices:
                # 0: icao24, 1: callsign, 2: origin_country, 3: time_position,
                # 4: last_contact, 5: longitude, 6: latitude, 7: baro_altitude,
                # 8: on_ground, 9: velocity, 10: true_track, 11: vertical_rate,
                # 12: sensors, 13: geo_altitude, 14: squawk, 15: spi, 16: position_source
                
                flight = {
                    "callsign": state[1].strip() if state[1] else "Unknown",
                    "country": state[2] if state[2] else "Unknown",
                    "lat": state[6],
                    "lon": state[5],
                    "altitude": state[7] or state[13] or 0,  # baro or geo altitude
                    "speed": state[9] if state[9] else 0,
                    "heading": state[10] if state[10] else 0,
                    "squawk": state[14] if state[14] else "1200",
                    "on_ground": state[8] if state[8] else False,
                    "last_contact": state[4],
                    "source": "OpenSky"
                }
                
                # Determine if emergency (squawk codes 7500, 7600, 7700)
                flight["is_emergency"] = flight["squawk"] in ["7500", "7600", "7700"]
                
                # Only include flights with valid coordinates
                if flight["lat"] is not None and flight["lon"] is not None:
                    flights.append(flight)
                    
            except (IndexError, TypeError, ValueError) as e:
                logger.debug(f"Error parsing flight state: {e}")
                continue
        
        return flights
    
    async def _get_adsb_flights(self) -> List[Dict]:
        """Fetch flights from ADS-B Exchange (if API key is available)"""
        
        if not self.adsb_key:
            logger.debug("No ADS-B Exchange API key configured")
            return []
        
        try:
            headers = {'api-auth': self.adsb_key} if self.adsb_key else {}
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.adsb_url, headers=headers) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        flights = self._parse_adsb_data(data)
                        logger.info(f"✅ ADS-B Exchange: {len(flights)} flights")
                        return flights
                    else:
                        logger.warning(f"ADS-B Exchange returned {response.status}")
                        return []
                        
        except asyncio.TimeoutError:
            logger.warning("ADS-B Exchange timeout")
        except Exception as e:
            logger.warning(f"ADS-B Exchange error: {e}")
        
        return []
    
    def _parse_adsb_data(self, data: Dict) -> List[Dict]:
        """Parse ADS-B Exchange response"""
        flights = []
        aircraft = data.get("aircraft", [])
        
        for ac in aircraft[:100]:
            try:
                flight = {
                    "callsign": ac.get("flight", "Unknown").strip(),
                    "lat": ac.get("lat"),
                    "lon": ac.get("lon"),
                    "altitude": ac.get("alt_baro", 0),
                    "speed": ac.get("speed", 0),
                    "heading": ac.get("track", 0),
                    "squawk": ac.get("squawk", "1200"),
                    "on_ground": ac.get("alt_baro") == "ground",
                    "source": "ADS-B Exchange"
                }
                
                flight["is_emergency"] = flight["squawk"] in ["7500", "7600", "7700"]
                
                if flight["lat"] is not None and flight["lon"] is not None:
                    flights.append(flight)
                    
            except Exception as e:
                logger.debug(f"Error parsing ADS-B aircraft: {e}")
                continue
        
        return flights
    
    def _filter_by_distance(self, flights: List[Dict], center_lat: float, center_lon: float, radius_km: float) -> List[Dict]:
        """Filter flights by distance from center point"""
        nearby = []
        
        for flight in flights:
            if flight["lat"] is None or flight["lon"] is None:
                continue
            
            dist = self._calculate_distance(
                center_lat, center_lon,
                flight["lat"], flight["lon"]
            )
            
            if dist <= radius_km:
                flight["distance_km"] = round(dist, 1)
                nearby.append(flight)
        
        # Sort by distance
        return sorted(nearby, key=lambda x: x.get("distance_km", float('inf')))
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km using Haversine formula"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def _get_mock_flights(self, center_lat: float, center_lon: float, radius_km: float) -> List[Dict]:
        """Generate realistic mock flight data when all sources fail"""
        
        callsign_prefixes = ['DAL', 'UAL', 'AAL', 'JBU', 'SWA', 'BAW', 'KLM', 'AFR', 'LUF', 'RCH']
        airlines = ['Delta', 'United', 'American', 'JetBlue', 'Southwest', 'British', 'KLM', 'Air France', 'Lufthansa', 'US Air Force']
        
        flights = []
        num_flights = random.randint(8, 15)
        
        for i in range(num_flights):
            # Random position within radius
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(10, radius_km)
            
            # Convert polar to Cartesian offset
            lat_offset = (distance / 111) * math.cos(angle)  # 111 km per degree latitude
            lon_offset = (distance / (111 * math.cos(math.radians(center_lat)))) * math.sin(angle)
            
            lat = center_lat + lat_offset
            lon = center_lon + lon_offset
            
            # Random altitude between 5000 and 40000 feet
            altitude = random.randint(5000, 40000)
            
            # Random speed between 200 and 550 knots
            speed = random.randint(200, 550)
            
            # Random heading
            heading = random.randint(0, 359)
            
            # Determine if emergency (about 10% of flights)
            is_emergency = random.random() < 0.1
            squawk = random.choice(["7500", "7600", "7700"]) if is_emergency else str(random.randint(1000, 7777))
            
            # Generate callsign
            prefix = random.choice(callsign_prefixes)
            number = random.randint(100, 999)
            callsign = f"{prefix}{number}"
            
            flight = {
                "callsign": callsign,
                "country": random.choice(['USA', 'UK', 'France', 'Germany', 'Canada']),
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "altitude": altitude,
                "speed": speed,
                "heading": heading,
                "squawk": squawk,
                "is_emergency": is_emergency,
                "on_ground": altitude < 1000,
                "distance_km": round(distance, 1),
                "airline": random.choice(airlines),
                "source": "Mock Data (Enhanced)",
                "last_contact": int(time.time()) - random.randint(0, 300)
            }
            
            flights.append(flight)
        
        # Sort by distance
        flights.sort(key=lambda x: x["distance_km"])
        
        logger.info(f"Generated {len(flights)} mock flights near location")
        return flights
    
    async def get_emergency_flights(self, lat: float = 20.0, lon: float = 0.0, radius_km: float = 1000) -> List[Dict]:
        """Get all flights with emergency squawk codes within radius"""
        
        # Get flights (from cache, API, or mock)
        flights = await self.get_flights_near_location(lat, lon, radius_km)
        
        # Filter for emergency flights
        emergency = [f for f in flights if f.get("is_emergency", False)]
        
        logger.info(f"Found {len(emergency)} emergency flights")
        return emergency
    
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
            "squawk": flight.get("squawk"),
            "is_emergency": flight.get("is_emergency", False),
            "on_ground": flight.get("on_ground", False),
            "distance_km": flight.get("distance_km"),
            "source": flight.get("source", "Unknown"),
            "color": "#ff4444" if flight.get("is_emergency") else "#4CAF50",
            "icon": "emergency" if flight.get("is_emergency") else "flight"
        }