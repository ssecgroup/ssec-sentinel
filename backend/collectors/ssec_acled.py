"""ACLED Conflict Data Collector - Fixed OAuth Version"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from cachetools import TTLCache
import time
import asyncio

logger = logging.getLogger(__name__)

class ACLEDCollector:
    """Collects conflict data from ACLED API using OAuth authentication"""
    
    def __init__(self, username: str, password: str):
        """Initialize with your ACLED credentials"""
        self.username = username
        self.password = password
        self.base_url = "https://acleddata.com/api/acled/read"
        self.token_url = "https://acleddata.com/oauth/token"
        self.cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour cache
        
        # Token management
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.max_retries = 3
        
        logger.info(f"ACLED Collector initialized for user: {username}")
    
    def _get_new_token(self) -> Optional[Dict]:
        """Get new access token using username/password"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Requesting new token from {self.token_url} (attempt {attempt + 1})")
                
                response = requests.post(
                    self.token_url,
                    data={
                        'username': self.username,
                        'password': self.password,
                        'grant_type': 'password',
                        'client_id': 'acled'
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    timeout=30
                )
                
                logger.info(f"Token response status: {response.status_code}")
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    self.access_token = token_data['access_token']
                    self.refresh_token = token_data.get('refresh_token')
                    self.token_expiry = time.time() + token_data['expires_in']
                    
                    logger.info(f"✅ Successfully obtained ACLED token (expires in {token_data['expires_in']}s)")
                    return token_data
                else:
                    logger.error(f"❌ Token request failed: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Token request error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error("All token request attempts failed")
                    return None
        
        return None
    
    def _refresh_access_token(self) -> Optional[Dict]:
        """Refresh expired access token using refresh token"""
        if not self.refresh_token:
            logger.warning("No refresh token available, getting new token")
            return self._get_new_token()
        
        try:
            logger.info("Refreshing access token")
            response = requests.post(
                self.token_url,
                data={
                    'refresh_token': self.refresh_token,
                    'grant_type': 'refresh_token',
                    'client_id': 'acled'
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                self.access_token = token_data['access_token']
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data['refresh_token']
                self.token_expiry = time.time() + token_data['expires_in']
                
                logger.info("✅ Successfully refreshed ACLED token")
                return token_data
            else:
                logger.error(f"❌ Token refresh failed: {response.status_code}")
                return self._get_new_token()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Token refresh error: {e}")
            return self._get_new_token()
    
    def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid token before making API calls"""
        if not self.access_token or time.time() >= self.token_expiry - 60:  # 60s buffer
            logger.info("Token missing or expired, refreshing...")
            result = self._refresh_access_token()
            return result is not None
        return True
    
    def _make_api_request(self, params: Dict) -> Optional[Dict]:
        """Make authenticated request to ACLED API with proper headers"""
        if not self._ensure_valid_token():
            logger.error("Cannot make API request - no valid token")
            return None
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ssec-sentinel/0.3 (https://ssec-sentinel.vercel.app)'
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making API request to {self.base_url} (attempt {attempt + 1})")
                
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                
                logger.info(f"API response status: {response.status_code}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    logger.warning("Got 403, token might be expired - refreshing")
                    self._refresh_access_token()
                    headers['Authorization'] = f'Bearer {self.access_token}'
                elif response.status_code == 429:
                    logger.warning("Rate limited, waiting before retry...")
                    time.sleep(5 * (attempt + 1))
                else:
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
            
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        logger.error("All API request attempts failed")
        return None
    
    async def fetch_conflicts(self, 
                             country: Optional[str] = None,
                             days_back: int = 7,
                             min_fatalities: int = 0,
                             event_type: Optional[str] = None) -> List[Dict]:
        """Fetch recent conflict events from ACLED"""
        
        # Check cache first
        cache_key = f"{country}_{days_back}_{min_fatalities}_{event_type}"
        if cache_key in self.cache:
            logger.info(f"Returning cached conflicts for {cache_key}")
            return self.cache[cache_key]
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Build query parameters
            params = {
                '_format': 'json',
                'event_date': f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
                'event_date_where': 'BETWEEN',
                'limit': 1000,
                'fields': 'event_id_cnty,event_date,event_type,sub_event_type,actor1,actor2,country,location,latitude,longitude,fatalities,notes'
            }
            
            # Add optional filters
            if country:
                params['country'] = country
                logger.info(f"Filtering by country: {country}")
            
            if event_type:
                params['event_type'] = event_type
            
            if min_fatalities > 0:
                params['fatalities'] = f">{min_fatalities}"
            
            logger.info(f"Fetching conflicts from {start_date.date()} to {end_date.date()}")
            
            # Make the API request
            data = self._make_api_request(params)
            
            if data and data.get('status') == 200:
                conflicts = data.get('data', [])
                logger.info(f"✅ Successfully fetched {len(conflicts)} real conflicts from ACLED")
                
                # Cache results
                self.cache[cache_key] = conflicts
                return conflicts
            else:
                logger.warning("No data returned from ACLED API")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching ACLED data: {e}")
            return []
    
    def format_for_dashboard(self, event: Dict) -> Dict:
        """Convert ACLED event to dashboard format"""
        
        # Determine severity and color based on fatalities
        fatalities = int(event.get("fatalities", 0))
        
        if fatalities >= 10:
            severity = "CRITICAL"
            alert_level = "RED"
            color = "#ff4444"
        elif fatalities >= 5:
            severity = "HIGH"
            alert_level = "RED"
            color = "#ff6666"
        elif fatalities >= 1:
            severity = "MODERATE"
            alert_level = "ORANGE"
            color = "#ff8844"
        else:
            severity = "LOW"
            alert_level = "GREEN"
            color = "#4CAF50"
        
        # Get event type icon
        event_type = event.get("event_type", "")
        icons = {
            "Battles": "⚔️",
            "Explosions/Remote violence": "💥",
            "Violence against civilians": "👥",
            "Riots": "🔥",
            "Protests": "✊",
            "Strategic developments": "📋"
        }
        icon = icons.get(event_type, "⚠️")
        
        return {
            "id": f"acled-{event.get('event_id_cnty', '')}",
            "title": f"{icon} {event_type} - {event.get('location', 'Unknown')}",
            "type": event_type,
            "sub_type": event.get("sub_event_type", ""),
            "lat": float(event.get("latitude", 0)),
            "lon": float(event.get("longitude", 0)),
            "alertLevel": alert_level,
            "severity": severity,
            "color": color,
            "timestamp": event.get("event_date"),
            "description": event.get("notes", "")[:200] if event.get("notes") else "",
            "fatalities": fatalities,
            "actors": {
                "actor1": event.get("actor1", "Unknown"),
                "actor2": event.get("actor2", "Unknown")
            },
            "country": event.get("country", ""),
            "region": event.get("admin1", ""),
            "source": "ACLED",
            "tags": event.get("tags", "").split(";") if event.get("tags") else []
        }
    
    async def get_conflict_stats(self, country: Optional[str] = None) -> Dict:
        """Get conflict statistics"""
        conflicts = await self.fetch_conflicts(country, days_back=30)
        
        stats = {
            "total_events": len(conflicts),
            "total_fatalities": 0,
            "by_type": {},
            "by_country": {},
            "by_severity": {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0}
        }
        
        for event in conflicts:
            fatalities = int(event.get("fatalities", 0))
            stats["total_fatalities"] += fatalities
            
            # Count by type
            event_type = event.get("event_type", "Unknown")
            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1
            
            # Count by country
            country_name = event.get("country", "Unknown")
            stats["by_country"][country_name] = stats["by_country"].get(country_name, 0) + 1
            
            # Count by severity
            if fatalities >= 10:
                stats["by_severity"]["CRITICAL"] += 1
            elif fatalities >= 5:
                stats["by_severity"]["HIGH"] += 1
            elif fatalities >= 1:
                stats["by_severity"]["MODERATE"] += 1
            else:
                stats["by_severity"]["LOW"] += 1
        
        return stats