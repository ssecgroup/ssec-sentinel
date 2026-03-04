"""HDX Signals Collector - Fixed Version with Proper Headers and Retry Logic"""
import requests
import asyncio
import aiohttp
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
from cachetools import TTLCache
import time

logger = logging.getLogger(__name__)

class HDXSignalsCollector:
    """Collects automated crisis alerts from HDX Signals with fallback"""
    
    def __init__(self):
        self.base_url = "https://hapi.humdata.org/api/v1/signals"
        self.cache = TTLCache(maxsize=20, ttl=300)  # 5 minute cache
        
        # Request settings
        self.timeout = 15  # seconds
        self.max_retries = 3
        self.retry_delay = 2  # seconds base delay
        
        # Alternative sources when HDX fails
        self.reliefweb_url = "https://api.reliefweb.int/v1/reports"
        self.gdacs_url = "https://gdacs.org/xml/rss.xml"  # GDACS RSS feed
        
        # User agent (required by many APIs)
        self.user_agent = 'ssec-sentinel/0.3 (https://ssec-sentinel.vercel.app)'
        
        logger.info("HDX Signals Collector initialized")
    
    async def get_signals(self, severity: Optional[str] = None) -> List[Dict]:
        """Get automated crisis alerts from multiple sources"""
        
        # Check cache first
        cache_key = f"signals_{severity}"
        if cache_key in self.cache:
            logger.info(f"Returning cached signals for {cache_key}")
            return self.cache[cache_key]
        
        logger.info("Fetching crisis signals from multiple sources")
        
        # Try HDX first
        signals = await self._fetch_hdx_signals()
        
        if signals:
            logger.info(f"✅ Retrieved {len(signals)} signals from HDX")
            
        else:
            # Try ReliefWeb as fallback
            logger.info("HDX failed, trying ReliefWeb")
            signals = await self._fetch_reliefweb_reports()
            
            if signals:
                logger.info(f"✅ Retrieved {len(signals)} reports from ReliefWeb")
            
            else:
                # Try GDACS as second fallback
                logger.info("ReliefWeb failed, trying GDACS")
                signals = await self._fetch_gdacs_alerts()
                
                if signals:
                    logger.info(f"✅ Retrieved {len(signals)} alerts from GDACS")
                
                else:
                    # All sources failed - use mock data
                    logger.warning("All signal sources failed, using mock data")
                    signals = self._get_mock_signals()
        
        # Filter by severity if requested
        if severity and signals:
            signals = [s for s in signals if s.get("severity", "").lower() == severity.lower()]
        
        # Cache results
        if signals:
            self.cache[cache_key] = signals
        
        return signals
    
    async def _fetch_hdx_signals(self) -> List[Dict]:
        """Fetch signals from HDX API with proper headers"""
        
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        params = {
            'limit': 20,
            'sort': '-date'
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"HDX Signals attempt {attempt + 1}/{self.max_retries}")
                
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(
                        self.base_url,
                        params=params,
                        headers=headers
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            signals = self._parse_hdx_signals(data)
                            return signals
                        
                        elif response.status == 403:
                            logger.warning(f"HDX access forbidden (attempt {attempt + 1})")
                            # Try alternative authentication method
                            if attempt == 1:  # Try with different headers on second attempt
                                headers['Authorization'] = 'Bearer public'  # Some APIs accept public token
                            
                        elif response.status == 429:
                            logger.warning(f"HDX rate limited (attempt {attempt + 1})")
                            wait_time = self.retry_delay * (2 ** attempt) * 2
                            
                        else:
                            logger.warning(f"HDX returned {response.status} (attempt {attempt + 1})")
                            wait_time = self.retry_delay * (2 ** attempt)
                
            except asyncio.TimeoutError:
                logger.warning(f"HDX timeout (attempt {attempt + 1})")
                wait_time = self.retry_delay * (2 ** attempt)
                
            except aiohttp.ClientConnectorError as e:
                logger.warning(f"HDX connection error (attempt {attempt + 1}): {e}")
                wait_time = self.retry_delay * (2 ** attempt)
                
            except Exception as e:
                logger.warning(f"HDX unexpected error (attempt {attempt + 1}): {e}")
                wait_time = self.retry_delay * (2 ** attempt)
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        logger.error("All HDX attempts failed")
        return []
    
    def _parse_hdx_signals(self, data: Dict) -> List[Dict]:
        """Parse HDX Signals API response"""
        signals = []
        
        try:
            # HDX Signals response structure may vary
            items = data.get('data', [])
            
            for item in items:
                # Extract fields with fallbacks
                signal = {
                    "id": item.get('id', f"hdx-{len(signals)}"),
                    "headline": item.get('headline', item.get('title', 'Crisis Alert')),
                    "summary": item.get('summary', item.get('description', 'No description available')),
                    "severity": self._determine_severity(item),
                    "source": "HDX Signals",
                    "timestamp": item.get('published_date', item.get('date', datetime.utcnow().isoformat())),
                    "trend": item.get('trend', 'Stable'),
                    "country": item.get('country', item.get('location', 'Unknown')),
                    "url": item.get('url', '#')
                }
                
                # Add location if available
                if 'lat' in item and 'lon' in item:
                    signal['lat'] = float(item['lat'])
                    signal['lon'] = float(item['lon'])
                
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error parsing HDX signals: {e}")
        
        return signals
    
    def _determine_severity(self, item: Dict) -> str:
        """Determine severity from signal data"""
        
        # Check explicit severity field
        severity = item.get('severity', '').lower()
        if severity in ['high', 'medium', 'low']:
            return severity
        
        # Check for severity in tags or categories
        tags = item.get('tags', [])
        categories = item.get('categories', [])
        
        for tag in tags + categories:
            tag_lower = tag.lower()
            if 'critical' in tag_lower or 'emergency' in tag_lower or 'severe' in tag_lower:
                return 'high'
            elif 'warning' in tag_lower or 'watch' in tag_lower:
                return 'medium'
            elif 'information' in tag_lower or 'update' in tag_lower:
                return 'low'
        
        # Check title/headline for keywords
        text = (item.get('headline', '') + ' ' + item.get('title', '') + ' ' + 
                item.get('description', '')).lower()
        
        if any(word in text for word in ['critical', 'emergency', 'urgent', 'severe']):
            return 'high'
        elif any(word in text for word in ['warning', 'alert', 'watch']):
            return 'medium'
        
        return 'medium'  # Default
    
    async def _fetch_reliefweb_reports(self) -> List[Dict]:
        """Fetch reports from ReliefWeb API as fallback"""
        
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json'
        }
        
        params = {
            'appname': 'ssec-sentinel',
            'limit': 10,
            'sort[]': '-date',
            'profile': 'minimum'
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.reliefweb_url,
                    params=params,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_reliefweb_data(data)
                    else:
                        logger.warning(f"ReliefWeb returned {response.status}")
                        return []
                        
        except Exception as e:
            logger.warning(f"ReliefWeb error: {e}")
            return []
    
    def _parse_reliefweb_data(self, data: Dict) -> List[Dict]:
        """Parse ReliefWeb API response"""
        signals = []
        
        try:
            items = data.get('data', [])
            
            for item in items:
                fields = item.get('fields', {})
                
                signal = {
                    "id": f"reliefweb-{item.get('id', len(signals))}",
                    "headline": fields.get('title', {}).get('value', 'Humanitarian Report'),
                    "summary": fields.get('body', {}).get('value', '')[:200],
                    "severity": 'medium',  # ReliefWeb doesn't provide severity
                    "source": "ReliefWeb",
                    "timestamp": fields.get('date', {}).get('created', datetime.utcnow().isoformat()),
                    "trend": 'New Report',
                    "country": fields.get('country', [{}])[0].get('name', 'Unknown') if fields.get('country') else 'Unknown',
                    "url": fields.get('href', '#')
                }
                
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error parsing ReliefWeb data: {e}")
        
        return signals
    
    async def _fetch_gdacs_alerts(self) -> List[Dict]:
        """Fetch alerts from GDACS RSS feed as second fallback"""
        
        try:
            # GDACS provides RSS feed for disasters
            # This is a simplified parser - in production you'd use feedparser
            import feedparser
            
            feed = feedparser.parse(self.gdacs_url)
            signals = []
            
            for entry in feed.entries[:10]:
                severity = 'low'
                if 'red' in entry.get('title', '').lower():
                    severity = 'high'
                elif 'orange' in entry.get('title', '').lower():
                    severity = 'medium'
                
                signal = {
                    "id": f"gdacs-{entry.get('id', len(signals))}",
                    "headline": entry.get('title', 'Disaster Alert'),
                    "summary": entry.get('summary', '')[:200],
                    "severity": severity,
                    "source": "GDACS",
                    "timestamp": entry.get('published', datetime.utcnow().isoformat()),
                    "trend": 'Active',
                    "country": self._extract_country_from_text(entry.get('title', '')),
                    "url": entry.get('link', '#')
                }
                
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.warning(f"GDACS error: {e}")
            return []
    
    def _extract_country_from_text(self, text: str) -> str:
        """Extract country name from text (simplified)"""
        # This is a simplified version - you might want a proper country name extractor
        countries = ['Haiti', 'Ukraine', 'Syria', 'Turkey', 'Afghanistan', 'Myanmar', 
                    'Sudan', 'Ethiopia', 'Somalia', 'Yemen', 'Indonesia', 'Philippines',
                    'Japan', 'Chile', 'Mexico', 'USA', 'Canada', 'Australia', 'India']
        
        for country in countries:
            if country in text:
                return country
        
        return 'Unknown'
    
    def _get_mock_signals(self) -> List[Dict]:
        """Generate realistic mock crisis signals when all sources fail"""
        
        return [
            {
                "id": "signal-1",
                "headline": "🚨 CRITICAL: Escalation in Eastern Ukraine",
                "summary": "Fighting intensifies near Donetsk with heavy artillery. Civilian casualties reported in residential areas.",
                "severity": "high",
                "source": "Mock Data (Enhanced)",
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "trend": "+25% vs last week",
                "country": "Ukraine",
                "lat": 48.0,
                "lon": 37.8,
                "url": "#",
                "tags": ["conflict", "civilian_casualties", "artillery"]
            },
            {
                "id": "signal-2",
                "headline": "⚠️ WARNING: Food security deteriorating in Haiti",
                "summary": "IPC Phase 4 (Emergency) likely in coming months due to ongoing violence and supply chain disruptions.",
                "severity": "medium",
                "source": "Mock Data (Enhanced)",
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                "trend": "Worsening",
                "country": "Haiti",
                "lat": 18.5,
                "lon": -72.3,
                "url": "#",
                "tags": ["food_security", "humanitarian", "IPC"]
            },
            {
                "id": "signal-3",
                "headline": "🌍 Sudan: Humanitarian access constraints",
                "summary": "Aid deliveries blocked in Darfur region. Urgent need for humanitarian corridor.",
                "severity": "high",
                "source": "Mock Data (Enhanced)",
                "timestamp": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
                "trend": "Critical",
                "country": "Sudan",
                "lat": 13.5,
                "lon": 30.0,
                "url": "#",
                "tags": ["humanitarian_access", "blockade", "aid"]
            },
            {
                "id": "signal-4",
                "headline": "🔥 Wildfires threaten communities in California",
                "summary": "Multiple wildfires burning across northern California. Thousands under evacuation orders.",
                "severity": "high",
                "source": "Mock Data (Enhanced)",
                "timestamp": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
                "trend": "Expanding",
                "country": "USA",
                "lat": 39.0,
                "lon": -121.0,
                "url": "#",
                "tags": ["wildfire", "evacuation", "disaster"]
            },
            {
                "id": "signal-5",
                "headline": "🌊 Tsunami warning after 7.2 earthquake in Pacific",
                "summary": "Tsunami waves observed in coastal areas. Evacuations underway in low-lying regions.",
                "severity": "high",
                "source": "Mock Data (Enhanced)",
                "timestamp": (datetime.utcnow() - timedelta(hours=18)).isoformat(),
                "trend": "Active",
                "country": "Indonesia",
                "lat": -8.5,
                "lon": 115.0,
                "url": "#",
                "tags": ["earthquake", "tsunami", "evacuation"]
            }
        ]
    
    async def check_for_new_alerts(self, last_check: datetime) -> List[Dict]:
        """Check for alerts since last check time"""
        
        # Get current signals
        signals = await self.get_signals()
        
        # Filter for new ones
        new_alerts = []
        for signal in signals:
            try:
                signal_time = datetime.fromisoformat(signal["timestamp"].replace("Z", "+00:00"))
                if signal_time > last_check:
                    new_alerts.append(signal)
            except (ValueError, KeyError):
                # If timestamp can't be parsed, include it (better safe than sorry)
                new_alerts.append(signal)
        
        logger.info(f"Found {len(new_alerts)} new alerts since {last_check.isoformat()}")
        return new_alerts