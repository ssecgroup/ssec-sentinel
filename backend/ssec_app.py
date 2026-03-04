"""ssec-Sentinel Main Application - Complete with Rate Limiting - v1.0.0"""
import sys
import os
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
import random
import traceback
import feedparser
import httpx

# Rate limiting imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uvicorn

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

    # Import collectors
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
        except Exception as e:
            logger.warning(f"⚠️ Could not import {class_name}: {e}")
            collectors[class_name] = None

    from ssec_config import config

    acled = collectors.get("ACLEDCollector")
    hdx = collectors.get("HDXCollector")
    views = collectors.get("VIEWSCollector")
    signals = collectors.get("HDXSignalsCollector")
    military = collectors.get("MilitaryBasesCollector")
    helplines = collectors.get("EnhancedHelplinesCollector")
    flights = collectors.get("FlightCollector")
    heatmap = collectors.get("HeatmapCollector")

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
        version="1.0.0",  # UPDATED to 1.0.0
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Initialize rate limiter
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Configure CORS - STRICT
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://ssec-sentinel.vercel.app"],  # ONLY your frontend
        allow_credentials=True,
        allow_methods=["GET"],  # Only GET requests
        allow_headers=["*"],
    )

    # Bot filtering middleware
    @app.middleware("http")
    async def filter_bots_and_log(request: Request, call_next):
        # Log request
        start_time = time.time()
        
        # Filter bots
        user_agent = request.headers.get("user-agent", "").lower()
        blocked_agents = ['bot', 'crawler', 'scraper', 'spider', 'curl', 'wget', 'python-requests']
        
        if any(agent in user_agent for agent in blocked_agents) and 'opensky' not in user_agent:
            logger.warning(f"Blocked bot: {user_agent[:100]} from {request.client.host}")
            return JSONResponse(
                status_code=403,
                content={"error": "Bots not allowed without API key"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Log performance
        duration = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
        
        return response

    logger.info("✅ Configured security middleware")

except Exception as e:
    logger.error(f"❌ FATAL: Failed to start application: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)


# ==================== ROOT ENDPOINTS ====================

@app.get("/")
@app.get("/api")
@app.get("/ssec")
@limiter.limit("30/minute")
async def root(request: Request):
    return {
        "message": "ssec-Sentinel API",
        "version": "1.0.0",  # UPDATED to 1.0.0
        "status": "operational",
        "collectors": {n: "available" if s else "unavailable" for n, s in available_collectors.items()},
        "endpoints": [
            "/", "/health", "/conflicts", "/flights/near", "/heatmap",
            "/signals", "/military-bases", "/helplines", "/news", "/dashboard"
        ]
    }


@app.get("/health")
@app.get("/api/health")
@app.get("/ssec/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",  # UPDATED to 1.0.0
        "service": "ssec-sentinel",
        "collectors": available_collectors,
    }


# ==================== CONFLICT ENDPOINTS ====================

@app.get("/conflicts")
@app.get("/api/conflicts")
@app.get("/ssec/api/conflicts")
@limiter.limit("100/minute")
async def get_conflicts(
    request: Request,
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
    
    return get_mock_conflicts()


# ==================== FLIGHT ENDPOINTS ====================

@app.get("/flights/near")
@app.get("/api/flights/near")
@app.get("/ssec/api/flights/near")
@limiter.limit("50/minute")
async def get_flights_near(
    request: Request,
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
    
    return get_mock_flights(lat, lon, radius)


@app.get("/flights/emergency")
@app.get("/api/flights/emergency")
@app.get("/ssec/api/flights/emergency")
@limiter.limit("30/minute")
async def get_emergency_flights(
    request: Request,
    lat: float = 20.0,
    lon: float = 0.0,
    radius: float = 1000
):
    """Get all flights with emergency squawk codes"""
    if flights and available_collectors["FlightCollector"]:
        try:
            emergency = await flights.get_emergency_flights(lat, lon, radius)
            return [flights.format_for_map(f) for f in emergency]
        except Exception as e:
            logger.error(f"Error fetching emergency flights: {e}")
    
    return [f for f in get_mock_flights(lat, lon, radius) if f.get("is_emergency")]


# ==================== HEATMAP ENDPOINTS ====================

@app.get("/heatmap")
@app.get("/api/heatmap")
@app.get("/ssec/api/heatmap")
@limiter.limit("30/minute")
async def get_heatmap(
    request: Request,
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


# ==================== HDX SIGNALS ====================

@app.get("/signals")
@app.get("/api/signals")
@app.get("/ssec/api/signals")
@limiter.limit("30/minute")
async def get_signals(request: Request, severity: Optional[str] = None):
    """Get automated crisis alerts"""
    if signals and available_collectors["HDXSignalsCollector"]:
        try:
            return await signals.get_signals(severity)
        except Exception as e:
            logger.error(f"Error fetching signals: {e}")
    
    return get_mock_signals()


# ==================== MILITARY BASES ====================

@app.get("/military-bases")
@app.get("/api/military-bases")
@app.get("/ssec/api/military-bases")
@limiter.limit("100/minute")
async def get_military_bases(request: Request, country: Optional[str] = None):
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
@limiter.limit("30/minute")
async def get_bases_near_conflict(
    request: Request,
    lat: float,
    lon: float,
    radius: float = 500
):
    """Find military bases near conflict zone"""
    if military and available_collectors["MilitaryBasesCollector"]:
        try:
            return military.get_bases_near_conflict(lat, lon, radius)
        except Exception as e:
            logger.error(f"Error finding nearby bases: {e}")
    
    return get_mock_bases_near(lat, lon)


# ==================== HELPLINES ====================

@app.get("/helplines")
@app.get("/api/helplines")
@app.get("/ssec/api/helplines")
@limiter.limit("100/minute")
async def get_helplines(
    request: Request,
    country: str = "US",
    helpline_type: Optional[str] = None
):
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


# ==================== RSS NEWS ====================

@app.get("/news")
@app.get("/api/news")
@app.get("/ssec/api/news")
@limiter.limit("60/minute")
async def get_rss_news(request: Request, limit: int = 15):
    """Aggregate news from multiple RSS feeds"""
    feeds = [
        'https://feeds.bbci.co.uk/news/world/rss.xml',
        'https://feeds.reuters.com/reuters/worldnews?format=xml',
        'https://www.aljazeera.com/xml/rss/all.xml',
        'https://feeds.npr.org/1001/rss.xml'
    ]
    
    all_entries = []
    headers = {'User-Agent': 'ssec-sentinel/1.0.0 (https://ssec-sentinel.vercel.app)'}  # UPDATED
    
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        for feed_url in feeds:
            try:
                response = await client.get(feed_url, follow_redirects=True)
                if response.status_code == 200:
                    feed = feedparser.parse(response.text)
                    feed_title = feed.feed.get('title', 'News') if hasattr(feed, 'feed') else 'News'
                    
                    for entry in feed.entries[:3]:
                        all_entries.append({
                            'id': entry.get('id', entry.get('link', len(all_entries))),
                            'title': entry.get('title', 'Untitled'),
                            'source': feed_title,
                            'timestamp': entry.get('published', entry.get('updated', datetime.utcnow().isoformat())),
                            'url': entry.get('link', '#'),
                            'summary': entry.get('summary', entry.get('description', ''))[:200],
                        })
            except Exception as e:
                logger.warning(f"Error fetching RSS {feed_url}: {e}")
    
    all_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    if not all_entries:
        return get_mock_news()
    
    return all_entries[:limit]


# ==================== DASHBOARD ====================

@app.get("/dashboard")
@app.get("/api/dashboard")
@app.get("/ssec/api/dashboard")
@limiter.limit("30/minute")
async def get_dashboard_data(request: Request, country: Optional[str] = None):
    """Get all data for dashboard in one request"""
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
        
        # Military bases
        if military and available_collectors["MilitaryBasesCollector"]:
            tasks.append(asyncio.to_thread(military.get_all_bases))
        else:
            tasks.append(as_coroutine(get_mock_military_bases()))
        
        # News
        tasks.append(get_rss_news(request, 5))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        conflicts_result, flights_result, signals_result, bases_result, news_result = results
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "total_conflicts": len(conflicts_result if not isinstance(conflicts_result, Exception) else []),
                "total_flights": len(flights_result if not isinstance(flights_result, Exception) else []),
                "emergency_flights": len([f for f in (flights_result if not isinstance(flights_result, Exception) else []) if f.get("is_emergency")]),
                "active_signals": len(signals_result if not isinstance(signals_result, Exception) else []),
                "military_bases": len(bases_result if not isinstance(bases_result, Exception) else []),
                "news_items": len(news_result if not isinstance(news_result, Exception) else [])
            },
            "conflicts": conflicts_result if not isinstance(conflicts_result, Exception) else get_mock_conflicts(),
            "flights": flights_result[:10] if not isinstance(flights_result, Exception) else get_mock_flights(20, 0, 500)[:10],
            "signals": signals_result if not isinstance(signals_result, Exception) else get_mock_signals(),
            "military_bases": bases_result if not isinstance(bases_result, Exception) else get_mock_military_bases(),
            "news": news_result if not isinstance(news_result, Exception) else get_mock_news(),
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {"total_conflicts": 3, "total_flights": 15, "emergency_flights": 2, "active_signals": 2, "military_bases": 5, "news_items": 5},
            "conflicts": get_mock_conflicts(),
            "flights": get_mock_flights(20, 0, 500)[:10],
            "signals": get_mock_signals(),
            "military_bases": get_mock_military_bases(),
            "news": get_mock_news(),
        }


# ==================== HELPER FUNCTIONS ====================

async def as_coroutine(value):
    return value


def _acled_has_credentials() -> bool:
    try:
        return bool(
            getattr(config, "ACLED_USERNAME", None) and
            getattr(config, "ACLED_PASSWORD", None) and
            config.ACLED_USERNAME not in ("", "demo", "demo_user") and
            config.ACLED_PASSWORD not in ("", "demo", "demo_pass")
        )
    except Exception:
        return False


# ==================== MOCK DATA FUNCTIONS ====================

def get_mock_conflicts():
    return [
        {"id": "conflict-1", "title": "⚔️ Battle - Damascus", "type": "Battles", "lat": 33.5, "lon": 36.3, "alertLevel": "RED", "color": "#ff4444", "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(), "description": "Heavy fighting in eastern suburbs", "fatalities": 23, "country": "Syria", "source": "ACLED (Mock)"},
        {"id": "conflict-2", "title": "💥 Explosion - Gaza", "type": "Explosions", "lat": 31.5, "lon": 34.5, "alertLevel": "RED", "color": "#ff6666", "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(), "description": "Airstrike in residential area", "fatalities": 12, "country": "Palestine", "source": "ACLED (Mock)"},
        {"id": "conflict-3", "title": "👥 Violence - Donetsk", "type": "Violence against civilians", "lat": 48.0, "lon": 37.8, "alertLevel": "ORANGE", "color": "#ff8844", "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(), "description": "Shelling of residential neighborhood", "fatalities": 5, "country": "Ukraine", "source": "ACLED (Mock)"},
    ]


def get_mock_flights(lat, lon, radius):
    callsigns = ['DAL123', 'UAL456', 'AAL789', 'JBU234', 'SWA567', 'BAW890']
    flights = []
    for i in range(random.randint(8, 12)):
        is_emergency = random.random() < 0.15
        flights.append({
            "callsign": callsigns[i % len(callsigns)],
            "lat": lat + (random.random() - 0.5) * (radius / 50),
            "lon": lon + (random.random() - 0.5) * (radius / 50),
            "altitude": random.randint(5000, 40000),
            "speed": random.randint(200, 550),
            "is_emergency": is_emergency,
            "squawk": "7700" if is_emergency else str(random.randint(1000, 7777)),
            "source": "Mock Data"
        })
    return flights


def get_mock_signals():
    return [
        {"id": "signal-1", "headline": "🚨 CRITICAL: Escalation in Eastern Ukraine", "summary": "Fighting intensifies near Donetsk", "severity": "high", "timestamp": datetime.utcnow().isoformat(), "trend": "+25% vs last week"},
        {"id": "signal-2", "headline": "⚠️ WARNING: Food security deteriorating in Haiti", "summary": "IPC Phase 4 likely in coming months", "severity": "medium", "timestamp": datetime.utcnow().isoformat(), "trend": "Worsening"},
        {"id": "signal-3", "headline": "🌍 Sudan: Humanitarian access constraints", "summary": "Aid deliveries blocked", "severity": "high", "timestamp": datetime.utcnow().isoformat(), "trend": "Critical"},
    ]


def get_mock_military_bases():
    return [
        {"name": "Ramstein Air Base", "icon": "🇺🇸", "lat": 49.4369, "lon": 7.6003, "country": "Germany"},
        {"name": "Camp Bondsteel", "icon": "🇺🇸", "lat": 42.3667, "lon": 21.25, "country": "Kosovo"},
        {"name": "Diego Garcia", "icon": "🇺🇸", "lat": -7.3133, "lon": 72.4111, "country": "BIOT"},
        {"name": "Tartus Naval Base", "icon": "🇷🇺", "lat": 34.9167, "lon": 35.8833, "country": "Syria"},
        {"name": "Khmeimim Air Base", "icon": "🇷🇺", "lat": 35.4167, "lon": 35.9333, "country": "Syria"},
    ]


def get_mock_bases_near(lat, lon):
    return [
        {"name": "Nearby Base Alpha", "distance_km": 45, "country": "Unknown", "lat": lat + 0.5, "lon": lon + 0.5},
        {"name": "Nearby Base Bravo", "distance_km": 78, "country": "Unknown", "lat": lat - 0.3, "lon": lon + 0.8},
    ]


def get_mock_helplines(country):
    return [
        {"name": "🚨 Emergency Services", "number": "112", "available": "24/7", "type": "emergency"},
        {"name": "❤️ Red Cross", "number": "+123456789", "available": "24/7", "type": "humanitarian"},
    ]


def get_mock_heatmap():
    points = []
    centers = [(33.5, 36.3), (31.5, 34.5), (48.0, 37.8)]
    for center in centers:
        for _ in range(20):
            points.append({
                "lat": center[0] + random.uniform(-2, 2),
                "lon": center[1] + random.uniform(-2, 2),
                "intensity": random.uniform(0.3, 1.0)
            })
    return points


def get_mock_news():
    return [
        {"title": "7.2 Earthquake Hits Caribbean", "source": "Reuters", "timestamp": datetime.utcnow().isoformat(), "url": "#", "summary": "Major earthquake triggers tsunami warnings"},
        {"title": "UN warns of famine risk in Gaza", "source": "BBC", "timestamp": datetime.utcnow().isoformat(), "url": "#", "summary": "Humanitarian situation worsens"},
        {"title": "Flooding in Southeast Asia displaces thousands", "source": "Al Jazeera", "timestamp": datetime.utcnow().isoformat(), "url": "#", "summary": "Monsoon floods affect millions"},
    ]


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ssec-Sentinel v1.0.0 Starting...")  # UPDATED
    print("=" * 60)
    print("\n📡 Endpoints available:")
    print("  • GET  /")
    print("  • GET  /health")
    print("  • GET  /conflicts")
    print("  • GET  /flights/near")
    print("  • GET  /heatmap")
    print("  • GET  /signals")
    print("  • GET  /military-bases")
    print("  • GET  /helplines")
    print("  • GET  /news")
    print("  • GET  /dashboard")
    print("\n📚 Documentation at: /docs")
    print("🎯 Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "ssec_app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # CHANGED to False for production
        log_level="info"
    )
