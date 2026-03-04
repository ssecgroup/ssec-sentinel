"""ssec-Sentinel Main Application - Complete Fixed Version"""
import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
import random
import traceback
import feedparser
import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

try:
    logger.info("=" * 60)
    logger.info("🚀 ssec-Sentinel v1.0.0 Starting...")
    logger.info("=" * 60)

    # Add backend to path
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.append(str(backend_dir))
    logger.info(f"✅ Added {backend_dir} to path")

    # Import FastAPI
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, Response
    import uvicorn

    logger.info("✅ Imported core modules")

    # Dynamic collector loading
    collectors = {}
    collector_classes = [
        ("ssec_acled", "ACLEDCollector", ["ACLED_USERNAME", "ACLED_PASSWORD"]),
        ("ssec_hdx", "HDXCollector", []),
        ("ssec_views", "VIEWSCollector", []),
        ("ssec_signals", "HDXSignalsCollector", []),
        ("ssec_military", "MilitaryBasesCollector", []),
        ("ssec_helplines_enhanced", "EnhancedHelplinesCollector", []),
        ("ssec_flights", "FlightCollector", []),
        ("ssec_heatmap", "HeatmapCollector", [])
    ]

    for module_name, class_name, config_params in collector_classes:
        try:
            module = __import__(f"collectors.{module_name}", fromlist=[class_name])
            collector_class = getattr(module, class_name)
            
            if config_params:
                from ssec_config import config
                args = [getattr(config, param) for param in config_params]
                collectors[class_name] = collector_class(*args)
            else:
                collectors[class_name] = collector_class()
                
            logger.info(f"✅ Imported and initialized {class_name}")
            
        except ImportError as e:
            logger.warning(f"⚠️ Could not import {class_name}: {e}")
            collectors[class_name] = None
        except Exception as e:
            logger.error(f"❌ Error initializing {class_name}: {e}")
            collectors[class_name] = None

    # Import config
    from ssec_config import config
    logger.info("✅ Imported config")

    # Assign collectors to variables
    acled = collectors.get("ACLEDCollector")
    hdx = collectors.get("HDXCollector")
    views = collectors.get("VIEWSCollector")
    signals = collectors.get("HDXSignalsCollector")
    military = collectors.get("MilitaryBasesCollector")
    helplines = collectors.get("EnhancedHelplinesCollector")
    flights = collectors.get("FlightCollector")
    heatmap = collectors.get("HeatmapCollector")

    # Track available collectors
    available_collectors = {
        "ACLEDCollector": acled is not None,
        "HDXCollector": hdx is not None,
        "VIEWSCollector": views is not None,
        "HDXSignalsCollector": signals is not None,
        "MilitaryBasesCollector": military is not None,
        "EnhancedHelplinesCollector": helplines is not None,
        "FlightCollector": flights is not None,
        "HeatmapCollector": heatmap is not None
    }
    
    logger.info(f"📊 Available collectors: {available_collectors}")

    # Create FastAPI app
    app = FastAPI(
        title="ssec-Sentinel API",
        description="Emergency Intelligence Platform with War Zone Monitoring",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    logger.info("✅ Created FastAPI app")

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("✅ Configured CORS")

except Exception as e:
    logger.error(f"❌ FATAL: Failed to start application: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)


# ==================== HELPER FUNCTIONS ====================

async def as_coroutine(value):
    """Wrap a plain value in a coroutine for asyncio.gather()"""
    return value


def _acled_has_credentials() -> bool:
    """Check if ACLED credentials are properly configured"""
    try:
        return bool(
            getattr(config, "ACLED_USERNAME", None) and
            getattr(config, "ACLED_PASSWORD", None) and
            config.ACLED_USERNAME not in ("", "demo", "demo_user") and
            config.ACLED_PASSWORD not in ("", "demo", "demo_pass")
        )
    except Exception:
        return False


# ==================== ROOT ENDPOINTS ====================

@app.get("/")
@app.get("/api")
@app.get("/ssec")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ssec-Sentinel API",
        "version": "1.0.0",
        "status": "operational",
        "collectors": {n: "available" if s else "unavailable" for n, s in available_collectors.items()},
        "endpoints": [
            "/",
            "/health",
            "/api/health",
            "/conflicts",
            "/api/conflicts",
            "/flights/near",
            "/api/flights/near",
            "/heatmap",
            "/api/heatmap",
            "/signals",
            "/api/signals",
            "/military-bases",
            "/api/military-bases",
            "/helplines",
            "/api/helplines",
            "/news",
            "/api/news",
            "/dashboard",
            "/api/dashboard",
            "/docs",
            "/redoc"
        ]
    }


@app.get("/health")
@app.get("/api/health")
@app.get("/ssec/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "ssec-sentinel",
        "collectors": available_collectors,
    }


# ==================== CONFLICT ENDPOINTS ====================

@app.get("/conflicts")
@app.get("/api/conflicts")
@app.get("/ssec/api/conflicts")
async def get_conflicts(
    country: Optional[str] = None,
    days: int = 7,
    min_fatalities: int = 0,
    event_type: Optional[str] = None,
):
    """Get conflict events from ACLED"""
    if acled and available_collectors["ACLEDCollector"]:
        try:
            events = await acled.fetch_conflicts(
                country=country,
                days_back=days,
                min_fatalities=min_fatalities
            )
            
            if events:
                formatted = [acled.format_for_dashboard(e) for e in events]
                if event_type:
                    formatted = [e for e in formatted if e["type"] == event_type]
                return formatted
            else:
                logger.info("No conflicts returned from ACLED, using mock data")
                
        except Exception as e:
            logger.error(f"Error fetching conflicts: {e}")
    
    # Fallback to mock data
    return get_mock_conflicts()


@app.get("/conflicts/stats")
@app.get("/api/conflicts/stats")
@app.get("/ssec/api/conflicts/stats")
async def get_conflict_stats(country: Optional[str] = None):
    """Get conflict statistics"""
    if acled and available_collectors["ACLEDCollector"]:
        try:
            return await acled.get_conflict_stats(country)
        except Exception as e:
            logger.error(f"Error fetching conflict stats: {e}")
    return get_mock_conflict_stats()


@app.get("/conflicts/hotspots")
@app.get("/api/conflicts/hotspots")
@app.get("/ssec/api/conflicts/hotspots")
async def get_hotspots(threshold: int = 10):
    """Get conflict hotspots (areas with most fatalities)"""
    if acled and available_collectors["ACLEDCollector"]:
        try:
            events = await acled.fetch_conflicts(days_back=30)
            hotspots = {}
            for e in events:
                loc = f"{e.get('latitude')},{e.get('longitude')}"
                if loc not in hotspots:
                    hotspots[loc] = {
                        "lat": e.get("latitude"),
                        "lon": e.get("longitude"),
                        "fatalities": 0,
                        "events": 0,
                        "location": e.get("location")
                    }
                hotspots[loc]["fatalities"] += int(e.get("fatalities", 0))
                hotspots[loc]["events"] += 1
            
            result = [h for h in hotspots.values() if h["fatalities"] >= threshold]
            return sorted(result, key=lambda x: x["fatalities"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error fetching hotspots: {e}")
    
    return get_mock_hotspots()


# ==================== FLIGHT ENDPOINTS ====================

@app.get("/flights/near")
@app.get("/api/flights/near")
@app.get("/ssec/api/flights/near")
async def get_flights_near(
    lat: float = 20.0,
    lon: float = 0.0,
    radius: float = 100,
    emergency_only: bool = False
):
    """Get flights near specific coordinates"""
    if flights and available_collectors["FlightCollector"]:
        try:
            result = await flights.get_flights_near_location(lat, lon, radius)
            if emergency_only:
                result = [f for f in result if f.get("is_emergency")]
            return [flights.format_for_map(f) for f in result]
        except Exception as e:
            logger.error(f"Error fetching flights: {e}")
    
    # Fallback to mock
    return get_mock_flights(lat, lon, radius)


@app.get("/flights/emergency")
@app.get("/api/flights/emergency")
@app.get("/ssec/api/flights/emergency")
async def get_emergency_flights(lat: float = 20.0, lon: float = 0.0, radius: float = 1000):
    """Get all flights with emergency squawk codes"""
    if flights and available_collectors["FlightCollector"]:
        try:
            emergency = await flights.get_emergency_flights(lat, lon, radius)
            return [flights.format_for_map(f) for f in emergency]
        except Exception as e:
            logger.error(f"Error fetching emergency flights: {e}")
    
    # Fallback to mock
    return [f for f in get_mock_flights(lat, lon, radius) if f.get("is_emergency")]


@app.get("/flights/near-disaster/{disaster_id}")
@app.get("/api/flights/near-disaster/{disaster_id}")
@app.get("/ssec/api/flights/near-disaster/{disaster_id}")
async def get_flights_near_disaster(disaster_id: str, radius: float = 100):
    """Get flights near a specific disaster"""
    # This would look up disaster coordinates, using mock for now
    nearby = get_mock_flights(18.5, -77.2, radius)
    return {
        "disaster_id": disaster_id,
        "aircraft_count": len(nearby),
        "aircraft": nearby[:10]
    }


# ==================== HEATMAP ENDPOINTS ====================

@app.get("/heatmap")
@app.get("/api/heatmap")
@app.get("/ssec/api/heatmap")
async def get_heatmap(
    disaster_type: Optional[str] = None,
    days: int = 30,
    points: int = 100
):
    """Get heatmap data for disasters and conflicts"""
    if heatmap and available_collectors["HeatmapCollector"]:
        try:
            return heatmap.generate_heatmap_data(
                disaster_type=disaster_type,
                days=days,
                points=points
            )
        except Exception as e:
            logger.error(f"Error generating heatmap: {e}")
    
    return get_mock_heatmap()


@app.get("/heatmap/conflicts")
@app.get("/api/heatmap/conflicts")
@app.get("/ssec/api/heatmap/conflicts")
async def get_conflict_heatmap(min_intensity: float = 0.7):
    """Get conflict-specific heatmap"""
    if heatmap and available_collectors["HeatmapCollector"]:
        try:
            return heatmap.get_conflict_hotspots(min_intensity)
        except Exception as e:
            logger.error(f"Error generating conflict heatmap: {e}")
    
    return [p for p in get_mock_heatmap() if random.random() > 0.5]


@app.get("/heatmap/natural")
@app.get("/api/heatmap/natural")
@app.get("/ssec/api/heatmap/natural")
async def get_natural_disaster_heatmap():
    """Get natural disaster heatmap"""
    if heatmap and available_collectors["HeatmapCollector"]:
        try:
            return heatmap.get_natural_disaster_hotspots()
        except Exception as e:
            logger.error(f"Error generating natural disaster heatmap: {e}")
    
    return get_mock_heatmap()


@app.get("/heatmap/grid")
@app.get("/api/heatmap/grid")
@app.get("/ssec/api/heatmap/grid")
async def get_heatmap_grid(resolution: float = 0.5):
    """Get density grid for raster heatmap"""
    if heatmap and available_collectors["HeatmapCollector"]:
        try:
            return heatmap.get_density_grid(resolution)
        except Exception as e:
            logger.error(f"Error generating heatmap grid: {e}")
    
    return get_mock_grid()


@app.get("/heatmap/timeline")
@app.get("/api/heatmap/timeline")
@app.get("/ssec/api/heatmap/timeline")
async def get_heatmap_timeline(hours: int = 24):
    """Get time-series heatmap data"""
    if heatmap and available_collectors["HeatmapCollector"]:
        try:
            return heatmap.get_time_series(hours)
        except Exception as e:
            logger.error(f"Error generating heatmap timeline: {e}")
    
    return get_mock_timeline(hours)


@app.get("/heatmap/stats")
@app.get("/api/heatmap/stats")
@app.get("/ssec/api/heatmap/stats")
async def get_heatmap_stats():
    """Get heatmap statistics"""
    if heatmap and available_collectors["HeatmapCollector"]:
        try:
            return heatmap.get_statistics()
        except Exception as e:
            logger.error(f"Error getting heatmap stats: {e}")
    
    return get_mock_heatmap_stats()


# ==================== HDX HUMANITARIAN DATA ====================

@app.get("/displacement")
@app.get("/api/displacement")
@app.get("/ssec/api/displacement")
async def get_displacement(country: Optional[str] = None):
    """Get displacement data from HDX"""
    if hdx and available_collectors["HDXCollector"]:
        try:
            data = await hdx.get_displacement(country)
            return [hdx.format_alert(d) for d in data]
        except Exception as e:
            logger.error(f"Error fetching displacement data: {e}")
    
    return get_mock_displacement()


@app.get("/food-security")
@app.get("/api/food-security")
@app.get("/ssec/api/food-security")
async def get_food_security(country: Optional[str] = None):
    """Get food security data"""
    if hdx and available_collectors["HDXCollector"]:
        try:
            return await hdx.get_food_security(country)
        except Exception as e:
            logger.error(f"Error fetching food security data: {e}")
    
    return get_mock_food_security()


# ==================== VIEWS FORECASTS ====================

@app.get("/forecasts")
@app.get("/api/forecasts")
@app.get("/ssec/api/forecasts")
async def get_forecasts(country: Optional[str] = None):
    """Get conflict risk forecasts"""
    if views and available_collectors["VIEWSCollector"]:
        try:
            return await views.get_forecasts(country)
        except Exception as e:
            logger.error(f"Error fetching forecasts: {e}")
    
    return get_mock_forecasts()


@app.get("/forecasts/heatmap")
@app.get("/api/forecasts/heatmap")
@app.get("/ssec/api/forecasts/heatmap")
async def get_forecast_heatmap(country: Optional[str] = None):
    """Get forecast data formatted for heatmap"""
    if views and available_collectors["VIEWSCollector"]:
        try:
            return await views.get_forecast_heatmap(country)
        except Exception as e:
            logger.error(f"Error generating forecast heatmap: {e}")
    
    return get_mock_forecast_heatmap()


@app.get("/forecasts/high-risk")
@app.get("/api/forecasts/high-risk")
@app.get("/ssec/api/forecasts/high-risk")
async def get_high_risk_zones(threshold: float = 70):
    """Get zones with high conflict risk"""
    if views and available_collectors["VIEWSCollector"]:
        try:
            return await views.get_high_risk_zones(threshold)
        except Exception as e:
            logger.error(f"Error fetching high risk zones: {e}")
    
    return [f for f in get_mock_forecasts() if f["risk_score"] >= threshold]


# ==================== HDX SIGNALS ====================

@app.get("/signals")
@app.get("/api/signals")
@app.get("/ssec/api/signals")
async def get_signals(severity: Optional[str] = None):
    """Get automated crisis alerts"""
    if signals and available_collectors["HDXSignalsCollector"]:
        try:
            return await signals.get_signals(severity)
        except Exception as e:
            logger.error(f"Error fetching signals: {e}")
    
    return get_mock_signals()


@app.get("/signals/check")
@app.get("/api/signals/check")
@app.get("/ssec/api/signals/check")
async def check_new_signals(background_tasks: BackgroundTasks):
    """Check for new alerts since last check"""
    if signals and available_collectors["HDXSignalsCollector"]:
        try:
            last_check = datetime.utcnow() - timedelta(minutes=5)
            new_alerts = await signals.check_for_new_alerts(last_check)
            
            if new_alerts:
                background_tasks.add_task(notify_new_alerts, new_alerts)
            
            return {"new_alerts": len(new_alerts), "alerts": new_alerts}
        except Exception as e:
            logger.error(f"Error checking new signals: {e}")
    
    return {"new_alerts": 0, "alerts": []}


async def notify_new_alerts(alerts):
    """Send notifications for new alerts (placeholder)"""
    logger.info(f"🔔 New alerts: {len(alerts)}")
    # Here you could add email, SMS, or push notifications


# ==================== MILITARY BASES ====================

@app.get("/military-bases")
@app.get("/api/military-bases")
@app.get("/ssec/api/military-bases")
async def get_military_bases(country: Optional[str] = None):
    """Get military installations"""
    if military and available_collectors["MilitaryBasesCollector"]:
        try:
            if country:
                return military.get_bases_by_country(country)
            return military.get_all_bases()
        except Exception as e:
            logger.error(f"Error fetching military bases: {e}")
    
    return get_mock_military_bases()


@app.get("/military-bases/near")
@app.get("/api/military-bases/near")
@app.get("/ssec/api/military-bases/near")
async def get_bases_near_conflict(lat: float, lon: float, radius: float = 500):
    """Find military bases near conflict zone"""
    if military and available_collectors["MilitaryBasesCollector"]:
        try:
            return military.get_bases_near_conflict(lat, lon, radius)
        except Exception as e:
            logger.error(f"Error finding nearby bases: {e}")
    
    return get_mock_bases_near(lat, lon)


# ==================== ENHANCED HELPLINES ====================

@app.get("/helplines")
@app.get("/api/helplines")
@app.get("/ssec/api/helplines")
async def get_helplines(country: str = "US", helpline_type: Optional[str] = None):
    """Get crisis helplines by country"""
    if helplines and available_collectors["EnhancedHelplinesCollector"]:
        try:
            helplines_list = helplines.get_helplines(country)
            
            if helpline_type:
                helplines_list = [h for h in helplines_list if h["type"] == helpline_type]
            
            return helplines_list
        except Exception as e:
            logger.error(f"Error fetching helplines: {e}")
    
    return get_mock_helplines(country)


@app.get("/helplines/search")
@app.get("/api/helplines/search")
@app.get("/ssec/api/helplines/search")
async def search_helplines(query: str):
    """Search helplines by name or number"""
    if helplines and available_collectors["EnhancedHelplinesCollector"]:
        try:
            return helplines.search_helplines(query)
        except Exception as e:
            logger.error(f"Error searching helplines: {e}")
    
    return []


@app.get("/helplines/countries")
@app.get("/api/helplines/countries")
@app.get("/ssec/api/helplines/countries")
async def get_available_countries():
    """Get list of countries with helpline data"""
    if helplines and available_collectors["EnhancedHelplinesCollector"]:
        try:
            return helplines.get_all_countries()
        except Exception as e:
            logger.error(f"Error getting countries: {e}")
    
    return ["US", "UA", "SY", "HT", "TR", "AF", "IQ", "YE", "JO", "LB"]


# ==================== RSS NEWS ENDPOINT ====================

@app.get("/news")
@app.get("/api/news")
@app.get("/ssec/api/news")
async def get_rss_news(limit: int = 15):
    """Aggregate news from multiple RSS feeds"""
    
    # RSS feeds with updated URLs
    feeds = [
        'https://feeds.bbci.co.uk/news/world/rss.xml',
        'https://feeds.reuters.com/reuters/worldnews?format=xml',
        'https://www.aljazeera.com/xml/rss/all.xml',
        'https://feeds.npr.org/1001/rss.xml',
        'https://www3.nhk.or.jp/nhkworld/en/news/rss.xml',
        'https://feeds.feedburner.com/ndtvnews-world-news',
        'https://www.wsws.org/rss/mrss-main.xml'
    ]
    
    all_entries = []
    headers = {
        'User-Agent': 'ssec-sentinel/0.3 (https://ssec-sentinel.vercel.app)'
    }
    
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        for feed_url in feeds:
            try:
                logger.info(f"Fetching RSS: {feed_url}")
                
                response = await client.get(feed_url, follow_redirects=True)
                
                if response.status_code == 200:
                    feed = feedparser.parse(response.text)
                    
                    # Get feed title
                    feed_title = feed.feed.get('title', 'News') if hasattr(feed, 'feed') else 'News'
                    
                    for entry in feed.entries[:3]:  # Top 3 from each
                        # Extract categories
                        categories = []
                        if hasattr(entry, 'tags'):
                            categories = [tag.term for tag in entry.tags[:2]]
                        
                        all_entries.append({
                            'id': entry.get('id', entry.get('link', len(all_entries))),
                            'title': entry.get('title', 'Untitled'),
                            'source': feed_title,
                            'timestamp': entry.get('published', entry.get('updated', datetime.utcnow().isoformat())),
                            'url': entry.get('link', '#'),
                            'summary': entry.get('summary', entry.get('description', ''))[:200],
                            'categories': categories
                        })
                        
                elif response.status_code == 404:
                    logger.warning(f"RSS feed not found: {feed_url}")
                else:
                    logger.warning(f"RSS feed {feed_url} returned {response.status_code}")
                    
            except httpx.TimeoutException:
                logger.warning(f"Timeout fetching RSS: {feed_url}")
            except Exception as e:
                logger.warning(f"Error fetching RSS {feed_url}: {e}")
    
    # Sort by timestamp (newest first)
    all_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Return limited number
    if not all_entries:
        logger.warning("No news from RSS feeds, using mock data")
        return get_mock_news()
    
    logger.info(f"✅ Retrieved {len(all_entries)} news items")
    return all_entries[:limit]


# ==================== MISC ENDPOINTS ====================

@app.get("/disasters")
@app.get("/api/disasters")
@app.get("/ssec/api/disasters")
async def get_mock_disasters_endpoint():
    """Mock disaster data endpoint"""
    return get_mock_disasters()


# ==================== DASHBOARD ENDPOINT ====================

@app.get("/dashboard")
@app.get("/api/dashboard")
@app.get("/ssec/api/dashboard")
async def get_dashboard_data(country: Optional[str] = None):
    """
    Get all data for dashboard in one request
    """
    try:
        tasks = []

        # Conflicts
        if acled and available_collectors["ACLEDCollector"] and _acled_has_credentials():
            tasks.append(acled.fetch_conflicts(country, days_back=7))
        else:
            tasks.append(as_coroutine(get_mock_conflicts()))

        # Flights
        if flights and available_collectors["FlightCollector"]:
            tasks.append(flights.get_flights_near_location(20, 0, 500))
        else:
            tasks.append(as_coroutine(get_mock_flights(20, 0, 500)))

        # Signals
        if signals and available_collectors["HDXSignalsCollector"]:
            tasks.append(signals.get_signals())
        else:
            tasks.append(as_coroutine(get_mock_signals()))

        # Forecasts
        if views and available_collectors["VIEWSCollector"]:
            tasks.append(views.get_forecasts(country))
        else:
            tasks.append(as_coroutine(get_mock_forecasts()))

        # Military bases
        if military and available_collectors["MilitaryBasesCollector"]:
            tasks.append(asyncio.to_thread(military.get_all_bases))
        else:
            tasks.append(as_coroutine(get_mock_military_bases()))

        # News
        tasks.append(get_rss_news(5))  # Top 5 news items

        # Heatmap
        if heatmap and available_collectors["HeatmapCollector"]:
            tasks.append(asyncio.to_thread(heatmap.generate_heatmap_data, None, 30, 100))
        else:
            tasks.append(as_coroutine(get_mock_heatmap()))

        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Unpack results
        (conflicts_result, flights_result, signals_result, 
         forecasts_result, bases_result, news_result, heatmap_result) = results

        # Handle each result (use mock if exception)
        formatted_conflicts = (
            [acled.format_for_dashboard(c) for c in conflicts_result] 
            if not isinstance(conflicts_result, Exception) and conflicts_result
            else get_mock_conflicts()
        )
        
        flights_list = (
            flights_result 
            if not isinstance(flights_result, Exception) and flights_result
            else get_mock_flights(20, 0, 500)
        )
        
        signals_list = (
            signals_result 
            if not isinstance(signals_result, Exception) and signals_result
            else get_mock_signals()
        )
        
        forecasts_list = (
            forecasts_result 
            if not isinstance(forecasts_result, Exception) and forecasts_result
            else get_mock_forecasts()
        )
        
        bases_list = (
            bases_result 
            if not isinstance(bases_result, Exception) and bases_result
            else get_mock_military_bases()
        )
        
        news_list = (
            news_result 
            if not isinstance(news_result, Exception) and news_result
            else get_mock_news()
        )
        
        heatmap_data = (
            heatmap_result 
            if not isinstance(heatmap_result, Exception) and heatmap_result
            else get_mock_heatmap()
        )

        # Calculate stats
        emergency_flights = [f for f in flights_list if f.get("is_emergency", False)]
        
        stats = {
            "total_conflicts": len(formatted_conflicts),
            "total_flights": len(flights_list),
            "emergency_flights": len(emergency_flights),
            "active_signals": len(signals_list),
            "military_bases": len(bases_list),
            "news_items": len(news_list)
        }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
            "conflicts": formatted_conflicts,
            "flights": [flights.format_for_map(f) for f in flights_list[:10]] if flights else flights_list[:10],
            "signals": signals_list,
            "forecasts": forecasts_list,
            "military_bases": bases_list,
            "news": news_list,
            "heatmap": heatmap_data,
        }

    except Exception as e:
        logger.error(f"Dashboard error: {e}\n{traceback.format_exc()}")
        # Return combined mock data
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "total_conflicts": 3,
                "total_flights": 15,
                "emergency_flights": 2,
                "active_signals": 2,
                "military_bases": 5,
                "news_items": 5
            },
            "conflicts": get_mock_conflicts(),
            "flights": get_mock_flights(20, 0, 500)[:10],
            "signals": get_mock_signals(),
            "forecasts": get_mock_forecasts(),
            "military_bases": get_mock_military_bases(),
            "news": get_mock_news(),
            "heatmap": get_mock_heatmap(),
        }


# ==================== MOCK DATA FUNCTIONS ====================

def get_mock_conflicts():
    """Generate realistic mock conflict data"""
    return [
        {
            "id": "conflict-1",
            "title": "⚔️ Battle - Damascus",
            "type": "Battles",
            "sub_type": "Armed clash",
            "lat": 33.5,
            "lon": 36.3,
            "alertLevel": "RED",
            "severity": "CRITICAL",
            "color": "#ff4444",
            "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "description": "Heavy fighting in eastern suburbs between government forces and opposition groups. Multiple casualties reported.",
            "fatalities": 23,
            "actors": {"actor1": "Government forces", "actor2": "Opposition groups"},
            "country": "Syria",
            "region": "Damascus",
            "source": "ACLED (Mock)"
        },
        {
            "id": "conflict-2",
            "title": "💥 Explosion - Gaza",
            "type": "Explosions",
            "sub_type": "Airstrike",
            "lat": 31.5,
            "lon": 34.5,
            "alertLevel": "RED",
            "severity": "HIGH",
            "color": "#ff6666",
            "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "description": "Airstrike in residential area near Gaza City. Buildings damaged, civilians among casualties.",
            "fatalities": 12,
            "actors": {"actor1": "Military", "actor2": "Civilians"},
            "country": "Palestine",
            "region": "Gaza",
            "source": "ACLED (Mock)"
        },
        {
            "id": "conflict-3",
            "title": "👥 Violence against civilians - Donetsk",
            "type": "Violence against civilians",
            "sub_type": "Attack",
            "lat": 48.0,
            "lon": 37.8,
            "alertLevel": "ORANGE",
            "severity": "MODERATE",
            "color": "#ff8844",
            "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "description": "Shelling of residential neighborhood in Donetsk. Several buildings damaged.",
            "fatalities": 5,
            "actors": {"actor1": "Separatists", "actor2": "Civilians"},
            "country": "Ukraine",
            "region": "Donetsk",
            "source": "ACLED (Mock)"
        },
    ]


def get_mock_conflict_stats():
    """Generate mock conflict statistics"""
    return {
        "total_events": 150,
        "total_fatalities": 450,
        "by_type": {
            "Battles": 80,
            "Explosions": 40,
            "Violence against civilians": 30
        },
        "by_country": {
            "Syria": 45,
            "Ukraine": 38,
            "Yemen": 25,
            "Myanmar": 22,
            "Ethiopia": 20
        },
        "by_severity": {
            "CRITICAL": 20,
            "HIGH": 45,
            "MODERATE": 50,
            "LOW": 35
        }
    }


def get_mock_hotspots():
    """Generate mock conflict hotspots"""
    return [
        {"lat": 33.5, "lon": 36.3, "fatalities": 230, "events": 45, "location": "Damascus", "country": "Syria"},
        {"lat": 31.5, "lon": 34.5, "fatalities": 180, "events": 38, "location": "Gaza City", "country": "Palestine"},
        {"lat": 48.5, "lon": 37.5, "fatalities": 150, "events": 42, "location": "Donetsk", "country": "Ukraine"},
        {"lat": 15.5, "lon": 47.5, "fatalities": 120, "events": 25, "location": "Mukalla", "country": "Yemen"},
        {"lat": 9.5, "lon": 30.0, "fatalities": 95, "events": 18, "location": "Bentiu", "country": "South Sudan"}
    ]


def get_mock_heatmap():
    """Generate mock heatmap data"""
    points = []
    base_points = [
        (18.5, -77.2, "earthquake"), (25.3, -86.5, "hurricane"), (14.5, 108.2, "flood"),
        (33.5, 36.3, "conflict"), (31.5, 34.5, "conflict"), (48.5, 37.5, "conflict"),
        (15.5, 47.5, "conflict"), (9.5, 30.0, "flood"), (-6.1, 105.4, "volcano")
    ]
    
    for lat, lon, type_name in base_points:
        for _ in range(10):
            points.append({
                "lat": lat + random.uniform(-2, 2),
                "lon": lon + random.uniform(-2, 2),
                "intensity": random.uniform(0.3, 1.0),
                "type": type_name
            })
    return points


def get_mock_grid():
    """Generate mock grid data for heatmap"""
    points = []
    for i in range(-3, 4):
        for j in range(-3, 4):
            points.append({
                "lat": 18.5 + i * 0.5,
                "lon": -77.2 + j * 0.5,
                "intensity": random.uniform(0.2, 0.9)
            })
    return points


def get_mock_timeline(hours=24):
    """Generate mock timeline data"""
    data = []
    now = datetime.now()
    for i in range(hours):
        if random.random() > 0.7:
            data.append({
                "lat": 18.5 + random.uniform(-2, 2),
                "lon": -77.2 + random.uniform(-2, 2),
                "intensity": random.uniform(0.4, 1.0),
                "timestamp": (now - timedelta(hours=i)).isoformat(),
                "type": random.choice(["conflict", "earthquake", "flood"])
            })
    return data


def get_mock_heatmap_stats():
    """Generate mock heatmap statistics"""
    return {
        "total_points": 500,
        "by_type": {"conflict": 300, "earthquake": 100, "flood": 80, "volcano": 20},
        "avg_intensity": 0.75,
        "max_intensity": 0.98,
        "min_intensity": 0.25,
        "active_zones": 12
    }


def get_mock_displacement():
    """Generate mock displacement data"""
    return [
        {
            "id": "disp-1",
            "title": "🏕️ Displacement - Syria",
            "type": "Displacement",
            "lat": 33.5,
            "lon": 36.3,
            "alertLevel": "RED",
            "description": "230,000 people displaced in northwest Syria due to recent hostilities",
            "population": 230000,
            "source": "HDX (Mock)",
            "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat()
        },
        {
            "id": "disp-2",
            "title": "🏕️ Displacement - Ukraine",
            "type": "Displacement",
            "lat": 48.5,
            "lon": 37.5,
            "alertLevel": "ORANGE",
            "description": "120,000 people displaced in Donetsk region",
            "population": 120000,
            "source": "HDX (Mock)",
            "timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat()
        },
        {
            "id": "disp-3",
            "title": "🏕️ Displacement - Sudan",
            "type": "Displacement",
            "lat": 15.5,
            "lon": 32.5,
            "alertLevel": "ORANGE",
            "description": "180,000 people displaced in Darfur region",
            "population": 180000,
            "source": "HDX (Mock)",
            "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat()
        }
    ]


def get_mock_food_security():
    """Generate mock food security data"""
    return [
        {"country": "Yemen", "phase": "IPC 5 (Catastrophe)", "population": 16000000, "trend": "worsening"},
        {"country": "South Sudan", "phase": "IPC 4 (Emergency)", "population": 6500000, "trend": "stable"},
        {"country": "Haiti", "phase": "IPC 4 (Emergency)", "population": 4500000, "trend": "worsening"},
        {"country": "Ethiopia", "phase": "IPC 3 (Crisis)", "population": 8000000, "trend": "improving"},
        {"country": "Sudan", "phase": "IPC 3 (Crisis)", "population": 7500000, "trend": "worsening"}
    ]


def get_mock_forecasts():
    """Generate mock forecast data"""
    return [
        {
            "country": "Syria",
            "lat": 33.5,
            "lon": 36.3,
            "risk_score": 85,
            "risk_level": "EXTREME",
            "forecast_month": f"{datetime.now().year}-{(datetime.now().month+1):02d}",
            "confidence": 0.82,
            "description": "Extreme risk of continued conflict in Damascus region"
        },
        {
            "country": "Ukraine",
            "lat": 48.5,
            "lon": 37.5,
            "risk_score": 78,
            "risk_level": "EXTREME",
            "forecast_month": f"{datetime.now().year}-{(datetime.now().month+1):02d}",
            "confidence": 0.79,
            "description": "High risk of continued fighting in Donetsk region"
        },
        {
            "country": "Yemen",
            "lat": 15.5,
            "lon": 47.5,
            "risk_score": 72,
            "risk_level": "HIGH",
            "forecast_month": f"{datetime.now().year}-{(datetime.now().month+2):02d}",
            "confidence": 0.71,
            "description": "High risk of conflict escalation in southern regions"
        },
        {
            "country": "Myanmar",
            "lat": 21.0,
            "lon": 96.0,
            "risk_score": 65,
            "risk_level": "HIGH",
            "forecast_month": f"{datetime.now().year}-{(datetime.now().month+1):02d}",
            "confidence": 0.68,
            "description": "High risk of continued resistance activity"
        },
        {
            "country": "Ethiopia",
            "lat": 9.0,
            "lon": 38.7,
            "risk_score": 58,
            "risk_level": "MEDIUM",
            "forecast_month": f"{datetime.now().year}-{(datetime.now().month+2):02d}",
            "confidence": 0.65,
            "description": "Medium risk of localized conflict in Amhara region"
        }
    ]


def get_mock_forecast_heatmap():
    """Generate mock forecast heatmap data"""
    return [
        {"lat": 33.5, "lon": 36.3, "intensity": 0.85, "color": "#8B0000", "risk_level": "EXTREME"},
        {"lat": 48.5, "lon": 37.5, "intensity": 0.78, "color": "#FF4444", "risk_level": "EXTREME"},
        {"lat": 15.5, "lon": 47.5, "intensity": 0.72, "color": "#FF4444", "risk_level": "HIGH"},
        {"lat": 21.0, "lon": 96.0, "intensity": 0.65, "color": "#FF8844", "risk_level": "HIGH"},
        {"lat": 9.0, "lon": 38.7, "intensity": 0.58, "color": "#FF8844", "risk_level": "MEDIUM"},
        {"lat": 4.5, "lon": 18.5, "intensity": 0.55, "color": "#FF8844", "risk_level": "MEDIUM"},
        {"lat": 33.0, "lon": 43.0, "intensity": 0.45, "color": "#4CAF50", "risk_level": "LOW"}
    ]


def get_mock_signals():
    """Generate mock crisis signals"""
    return [
        {
            "id": "signal-1",
            "headline": "🚨 CRITICAL: Escalation in Eastern Ukraine",
            "summary": "Fighting intensifies near Donetsk with heavy artillery. Civilian casualties reported.",
            "severity": "high",
            "source": "HDX (Mock)",
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "trend": "+25% vs last week",
            "country": "Ukraine",
            "lat": 48.0,
            "lon": 37.8,
            "color": "#FF4444"
        },
        {
            "id": "signal-2",
            "headline": "⚠️ WARNING: Food security deteriorating in Haiti",
            "summary": "IPC Phase 4 (Emergency) likely in coming months due to ongoing violence and supply chain disruptions.",
            "severity": "medium",
            "source": "HDX (Mock)",
            "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
            "trend": "Worsening",
            "country": "Haiti",
            "lat": 18.5,
            "lon": -72.3,
            "color": "#FF8844"
        },
        {
            "id": "signal-3",
            "headline": "🌍 Sudan: Humanitarian access constraints",
            "summary": "Aid deliveries blocked in Darfur region. Urgent need for humanitarian corridor.",
            "severity": "high",
            "source": "HDX (Mock)",
            "timestamp": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
            "trend": "Critical",
            "country": "Sudan",
            "lat": 13.5,
            "lon": 30.0,
            "color": "#FF4444"
        }
    ]


def get_mock_military_bases():
    """Generate mock military bases data"""
    return [
        {"name": "Ramstein Air Base", "icon": "🇺🇸", "type": "US Air Force", "lat": 49.4369, "lon": 7.6003, "country": "Germany"},
        {"name": "Camp Bondsteel", "icon": "🇺🇸", "type": "US Army", "lat": 42.3667, "lon": 21.25, "country": "Kosovo"},
        {"name": "Diego Garcia", "icon": "🇺🇸", "type": "US Navy", "lat": -7.3133, "lon": 72.4111, "country": "British Indian Ocean Territory"},
        {"name": "Tartus Naval Base", "icon": "🇷🇺", "type": "Russian Navy", "lat": 34.9167, "lon": 35.8833, "country": "Syria"},
        {"name": "Khmeimim Air Base", "icon": "🇷🇺", "type": "Russian Air Force", "lat": 35.4167, "lon": 35.9333, "country": "Syria"},
        {"name": "Camp Lemonnier", "icon": "🇺🇸", "type": "US Navy", "lat": 11.55, "lon": 43.15, "country": "Djibouti"},
        {"name": "Al Udeid Air Base", "icon": "🇺🇸", "type": "US Air Force", "lat": 25.117, "lon": 51.317, "country": "Qatar"}
    ]


def get_mock_bases_near(lat, lon):
    """Generate mock nearby bases"""
    return [
        {"name": "Forward Operating Base Alpha", "distance_km": 45, "country": "Unknown", "lat": lat + 0.5, "lon": lon + 0.5},
        {"name": "Camp Forward Bravo", "distance_km": 78, "country": "Unknown", "lat": lat - 0.3, "lon": lon + 0.8},
        {"name": "Air Base Charlie", "distance_km": 120, "country": "Unknown", "lat": lat - 0.8, "lon": lon + 1.2}
    ]


def get_mock_helplines(country: str):
    """Generate mock helplines for any country"""
    helplines_db = {
        "US": [
            {"name": "🚨 911 Emergency", "number": "911", "available": "24/7", "type": "emergency"},
            {"name": "🧠 988 Suicide & Crisis", "number": "988", "available": "24/7", "type": "mental_health"},
            {"name": "❤️ Red Cross", "number": "1-800-733-2767", "available": "24/7", "type": "humanitarian"},
            {"name": "🌪️ FEMA Disaster Assistance", "number": "1-800-621-3362", "available": "24/7", "type": "disaster"}
        ],
        "UA": [
            {"name": "🚨 Emergency Services", "number": "112", "available": "24/7", "type": "emergency"},
            {"name": "❤️ Ukrainian Red Cross", "number": "0 800 332 656", "available": "24/7", "type": "humanitarian"},
            {"name": "🏥 Medical Emergency", "number": "103", "available": "24/7", "type": "medical"}
        ],
        "SY": [
            {"name": "❤️ Syrian Red Crescent", "number": "+963 11 331 0666", "available": "24/7", "type": "humanitarian"},
            {"name": "🆘 ICRC Syria", "number": "+963 11 331 0667", "available": "24/7", "type": "humanitarian"}
        ]
    }
    
    return helplines_db.get(country, [
        {"name": "🚨 Emergency Services", "number": "112", "available": "24/7", "type": "emergency"},
        {"name": "❤️ Red Cross", "number": "+123456789", "available": "24/7", "type": "humanitarian"}
    ])


def get_mock_flights(lat, lon, radius):
    """Generate mock flight data"""
    callsigns = ['DAL123', 'UAL456', 'AAL789', 'JBU234', 'SWA567', 'BAW890', 'KLM123', 'AFR456']
    airlines = ['Delta', 'United', 'American', 'JetBlue', 'Southwest', 'British', 'KLM', 'Air France']
    
    flights = []
    for i in range(random.randint(8, 15)):
        is_emergency = random.random() < 0.15
        
        flights.append({
            "id": f"flight-{i}",
            "callsign": callsigns[i % len(callsigns)],
            "lat": lat + (random.random() - 0.5) * (radius / 50),
            "lon": lon + (random.random() - 0.5) * (radius / 50),
            "altitude": random.randint(5000, 40000),
            "speed": random.randint(200, 550),
            "heading": random.randint(0, 359),
            "is_emergency": is_emergency,
            "squawk": "7700" if is_emergency else str(random.randint(1000, 7777)),
            "airline": airlines[i % len(airlines)],
            "source": "Mock Data"
        })
    
    return flights


def get_mock_disasters():
    """Generate mock disaster data"""
    return [
        {"id": "EQ12345", "name": "Earthquake - Caribbean Sea", "type": "Earthquake", "lat": 18.5, "lon": -77.2, 
         "alertLevel": "RED", "magnitude": 6.7, "startTime": (datetime.utcnow() - timedelta(hours=3)).isoformat(), 
         "description": "Magnitude 6.7 earthquake near Jamaica. Tsunami warnings issued."},
        {"id": "TC67890", "name": "Tropical Storm - Gulf of Mexico", "type": "Cyclone", "lat": 25.3, "lon": -86.5, 
         "alertLevel": "ORANGE", "wind_speed": 85, "startTime": (datetime.utcnow() - timedelta(hours=6)).isoformat(), 
         "description": "Category 1 hurricane approaching Gulf Coast."},
        {"id": "FL54321", "name": "Flooding - Southeast Asia", "type": "Flood", "lat": 14.5, "lon": 108.2, 
         "alertLevel": "GREEN", "startTime": (datetime.utcnow() - timedelta(hours=12)).isoformat(), 
         "description": "Monsoon flooding in Vietnam. Thousands displaced."},
        {"id": "WF98765", "name": "Wildfire - California", "type": "Wildfire", "lat": 37.8, "lon": -122.4, 
         "alertLevel": "RED", "acres": 15000, "startTime": (datetime.utcnow() - timedelta(hours=24)).isoformat(), 
         "description": "Wildfire spreading rapidly in Northern California."}
    ]


def get_mock_news():
    """Generate mock news data"""
    return [
        {
            "title": "7.2 magnitude earthquake strikes Caribbean, tsunami warnings issued",
            "source": "Reuters",
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "url": "#",
            "summary": "Major earthquake triggers tsunami warnings for Caribbean islands.",
            "categories": ["disaster", "earthquake"]
        },
        {
            "title": "UN warns of famine risk in Gaza as humanitarian situation worsens",
            "source": "BBC News",
            "timestamp": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
            "url": "#",
            "summary": "UN officials warn of catastrophic food insecurity in Gaza.",
            "categories": ["conflict", "humanitarian"]
        },
        {
            "title": "Flooding in Southeast Asia displaces thousands, crops destroyed",
            "source": "Al Jazeera",
            "timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
            "url": "#",
            "summary": "Monsoon floods affect millions across Vietnam, Thailand, and Cambodia.",
            "categories": ["disaster", "flood"]
        },
        {
            "title": "WHO declares mpox global health emergency as cases surge",
            "source": "NPR",
            "timestamp": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
            "url": "#",
            "summary": "World Health Organization declares public health emergency.",
            "categories": ["health", "emergency"]
        },
        {
            "title": "Climate disasters cost global economy $250B in 2025, report finds",
            "source": "NHK World",
            "timestamp": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
            "url": "#",
            "summary": "Economic losses from climate-related disasters reach record high.",
            "categories": ["climate", "economy"]
        }
    ]


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    print("=" * 60)
    print(" ssec-Sentinel v1.0.0 Starting...")
    print("=" * 60)
    print("\n Endpoints available:")
    print("  • GET  /")
    print("  • GET  /health")
    print("  • GET  /conflicts")
    print("  • GET  /conflicts/stats")
    print("  • GET  /conflicts/hotspots")
    print("  • GET  /flights/near")
    print("  • GET  /flights/emergency")
    print("  • GET  /heatmap")
    print("  • GET  /heatmap/conflicts")
    print("  • GET  /heatmap/natural")
    print("  • GET  /heatmap/grid")
    print("  • GET  /heatmap/timeline")
    print("  • GET  /heatmap/stats")
    print("  • GET  /signals")
    print("  • GET  /forecasts")
    print("  • GET  /forecasts/high-risk")
    print("  • GET  /displacement")
    print("  • GET  /food-security")
    print("  • GET  /military-bases")
    print("  • GET  /military-bases/near")
    print("  • GET  /helplines")
    print("  • GET  /helplines/search")
    print("  • GET  /helplines/countries")
    print("  • GET  /news")
    print("  • GET  /dashboard")
    print("\n Documentation at: /docs")
    print(" Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "ssec_app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
