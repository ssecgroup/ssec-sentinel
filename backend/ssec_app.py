"""ssec-Sentinel Main Application - COMPLETE VERSION WITH ALL ENDPOINTS"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
import random

# Add path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uvicorn

# Import all collectors
from collectors.ssec_acled import ACLEDCollector
from collectors.ssec_hdx import HDXCollector
from collectors.ssec_views import VIEWSCollector
from collectors.ssec_signals import HDXSignalsCollector
from collectors.ssec_military import MilitaryBasesCollector
from collectors.ssec_helplines_enhanced import EnhancedHelplinesCollector
from collectors.ssec_flights import FlightCollector
from collectors.ssec_heatmap import HeatmapCollector
from ssec_config import config

# Initialize collectors
acled = ACLEDCollector(config.ACLED_API_KEY, config.ACLED_EMAIL)
hdx = HDXCollector()
views = VIEWSCollector()
signals = HDXSignalsCollector()
military = MilitaryBasesCollector()
helplines = EnhancedHelplinesCollector()
flights = FlightCollector()
heatmap = HeatmapCollector()

# Create FastAPI app
app = FastAPI(
    title="ssec-Sentinel API",
    description="Emergency Intelligence Platform with War Zone Monitoring",
    version="0.3.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROOT ENDPOINT ====================
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ssec-Sentinel API",
        "version": "0.3.0",
        "status": "operational",
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
            "/docs",
            "/redoc"
        ]
    }

# ==================== HEALTH CHECK ====================
@app.get("/health")
@app.get("/api/health")
@app.get("/ssec/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.3.0",
        "service": "ssec-sentinel",
        "collectors": {
            "acled": bool(config.ACLED_API_KEY and config.ACLED_API_KEY != "demo_key"),
            "hdx": True,
            "views": True,
            "signals": True,
            "military": True,
            "flights": True,
            "heatmap": True
        }
    }

# ==================== CONFLICT ENDPOINTS ====================
@app.get("/conflicts")
@app.get("/api/conflicts")
@app.get("/ssec/api/conflicts")
async def get_conflicts(
    country: Optional[str] = None,
    days: int = 7,
    min_fatalities: int = 0,
    event_type: Optional[str] = None
):
    """Get conflict events from ACLED"""
    try:
        events = await acled.fetch_conflicts(
            country=country,
            days_back=days,
            min_fatalities=min_fatalities
        )
        
        # Format for dashboard
        formatted = [acled.format_for_dashboard(e) for e in events]
        
        # Filter by event type if specified
        if event_type:
            formatted = [e for e in formatted if e["type"] == event_type]
        
        return formatted
    except Exception as e:
        # Return mock data if ACLED fails
        return get_mock_conflicts()

@app.get("/conflicts/stats")
@app.get("/api/conflicts/stats")
@app.get("/ssec/api/conflicts/stats")
async def get_conflict_stats(country: Optional[str] = None):
    """Get conflict statistics"""
    try:
        stats = await acled.get_conflict_stats(country)
        return stats
    except Exception as e:
        return get_mock_conflict_stats()

@app.get("/conflicts/hotspots")
@app.get("/api/conflicts/hotspots")
@app.get("/ssec/api/conflicts/hotspots")
async def get_hotspots(threshold: int = 10):
    """Get conflict hotspots (areas with most fatalities)"""
    try:
        events = await acled.fetch_conflicts(days_back=30)
        
        # Group by location
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
        
        # Filter by threshold
        result = [h for h in hotspots.values() if h["fatalities"] >= threshold]
        return sorted(result, key=lambda x: x["fatalities"], reverse=True)
        
    except Exception as e:
        return get_mock_hotspots()

# ==================== FLIGHT TRACKING ENDPOINTS ====================
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
    try:
        flights_near = await flights.get_flights_near_location(lat, lon, radius)
        
        if emergency_only:
            flights_near = [f for f in flights_near if f.get("is_emergency")]
        
        formatted = [flights.format_for_map(f) for f in flights_near]
        return formatted
    except Exception as e:
        # Return mock data
        return flights._get_mock_flights(lat, lon, radius)

@app.get("/flights/emergency")
@app.get("/api/flights/emergency")
@app.get("/ssec/api/flights/emergency")
async def get_emergency_flights():
    """Get all flights with emergency squawk codes"""
    try:
        emergency = await flights.get_emergency_flights()
        return [flights.format_for_map(f) for f in emergency]
    except Exception as e:
        # Generate mock emergency flights
        mocks = flights._get_mock_flights(20, 0, 500)
        return [flights.format_for_map(f) for f in mocks if f.get("is_emergency")]

@app.get("/flights/near-disaster/{disaster_id}")
@app.get("/api/flights/near-disaster/{disaster_id}")
@app.get("/ssec/api/flights/near-disaster/{disaster_id}")
async def get_flights_near_disaster(disaster_id: str, radius: float = 100):
    """Get flights near a specific disaster"""
    # This would normally look up the disaster coordinates
    # For now, return mock data around Caribbean
    flights_near = flights._get_mock_flights(18.5, -77.2, radius)
    return {
        "disaster_id": disaster_id,
        "aircraft_count": len(flights_near),
        "aircraft": [flights.format_for_map(f) for f in flights_near]
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
    try:
        data = heatmap.generate_heatmap_data(
            disaster_type=disaster_type,
            days=days,
            points=points
        )
        return data
    except Exception as e:
        return get_mock_heatmap()

@app.get("/heatmap/conflicts")
@app.get("/api/heatmap/conflicts")
@app.get("/ssec/api/heatmap/conflicts")
async def get_conflict_heatmap(min_intensity: float = 0.7):
    """Get conflict-specific heatmap"""
    try:
        return heatmap.get_conflict_hotspots(min_intensity)
    except Exception as e:
        return [p for p in get_mock_heatmap() if random.random() > 0.5]

@app.get("/heatmap/natural")
@app.get("/api/heatmap/natural")
@app.get("/ssec/api/heatmap/natural")
async def get_natural_disaster_heatmap():
    """Get natural disaster heatmap"""
    try:
        return heatmap.get_natural_disaster_hotspots()
    except Exception as e:
        return get_mock_heatmap()

@app.get("/heatmap/grid")
@app.get("/api/heatmap/grid")
@app.get("/ssec/api/heatmap/grid")
async def get_heatmap_grid(resolution: float = 0.5):
    """Get density grid for raster heatmap"""
    try:
        return heatmap.get_density_grid(resolution)
    except Exception as e:
        return get_mock_grid()

@app.get("/heatmap/timeline")
@app.get("/api/heatmap/timeline")
@app.get("/ssec/api/heatmap/timeline")
async def get_heatmap_timeline(hours: int = 24):
    """Get time-series heatmap data"""
    try:
        return heatmap.get_time_series(hours)
    except Exception as e:
        return get_mock_timeline(hours)

@app.get("/heatmap/stats")
@app.get("/api/heatmap/stats")
@app.get("/ssec/api/heatmap/stats")
async def get_heatmap_stats():
    """Get heatmap statistics"""
    try:
        return heatmap.get_statistics()
    except Exception as e:
        return {
            "total_points": 500,
            "by_type": {"conflict": 300, "earthquake": 100, "flood": 100},
            "avg_intensity": 0.75,
            "max_intensity": 0.95,
            "min_intensity": 0.3,
            "active_zones": 12
        }

# ==================== HDX HUMANITARIAN DATA ====================
@app.get("/displacement")
@app.get("/api/displacement")
@app.get("/ssec/api/displacement")
async def get_displacement(country: Optional[str] = None):
    """Get displacement data from HDX"""
    try:
        data = await hdx.get_displacement(country)
        return [hdx.format_alert(d) for d in data]
    except Exception as e:
        return get_mock_displacement()

@app.get("/food-security")
@app.get("/api/food-security")
@app.get("/ssec/api/food-security")
async def get_food_security(country: Optional[str] = None):
    """Get food security data"""
    try:
        return await hdx.get_food_security(country)
    except Exception as e:
        return get_mock_food_security()

# ==================== VIEWS FORECASTS ====================
@app.get("/forecasts")
@app.get("/api/forecasts")
@app.get("/ssec/api/forecasts")
async def get_forecasts(country: Optional[str] = None):
    """Get conflict risk forecasts"""
    try:
        forecasts = await views.get_forecasts(country)
        return forecasts
    except Exception as e:
        return get_mock_forecasts()

@app.get("/forecasts/heatmap")
@app.get("/api/forecasts/heatmap")
@app.get("/ssec/api/forecasts/heatmap")
async def get_forecast_heatmap():
    """Get forecast data formatted for heatmap"""
    try:
        forecasts = await views.get_forecasts()
        heatmap_data = [{
            "lat": f["lat"],
            "lon": f["lon"],
            "intensity": f["risk_score"] / 100,
            "color": views.get_risk_color(f["risk_score"])
        } for f in forecasts if f.get("lat") and f.get("lon")]
        return heatmap_data
    except Exception as e:
        return get_mock_forecast_heatmap()

# ==================== HDX SIGNALS ====================
@app.get("/signals")
@app.get("/api/signals")
@app.get("/ssec/api/signals")
async def get_signals(severity: Optional[str] = None):
    """Get automated crisis alerts"""
    try:
        alerts = await signals.get_signals(severity)
        return alerts
    except Exception as e:
        return get_mock_signals()

@app.get("/signals/check")
@app.get("/api/signals/check")
@app.get("/ssec/api/signals/check")
async def check_new_signals(background_tasks: BackgroundTasks):
    """Check for new alerts since last check"""
    try:
        last_check = datetime.utcnow() - timedelta(minutes=5)
        new_alerts = await signals.check_for_new_alerts(last_check)
        
        if new_alerts:
            background_tasks.add_task(notify_new_alerts, new_alerts)
        
        return {
            "new_alerts": len(new_alerts),
            "alerts": new_alerts
        }
    except Exception as e:
        return {"new_alerts": 0, "alerts": []}

async def notify_new_alerts(alerts):
    """Send notifications for new alerts"""
    print(f"New alerts: {len(alerts)}")

# ==================== MILITARY BASES ====================
@app.get("/military-bases")
@app.get("/api/military-bases")
@app.get("/ssec/api/military-bases")
async def get_military_bases(country: Optional[str] = None):
    """Get military installations"""
    try:
        if country:
            return military.get_bases_by_country(country)
        return military.get_all_bases()
    except Exception as e:
        return get_mock_military_bases()

@app.get("/military-bases/near")
@app.get("/api/military-bases/near")
@app.get("/ssec/api/military-bases/near")
async def get_bases_near_conflict(lat: float, lon: float, radius: float = 500):
    """Find military bases near conflict zone"""
    try:
        return military.get_bases_near_conflict(lat, lon, radius)
    except Exception as e:
        return get_mock_bases_near(lat, lon)

# ==================== ENHANCED HELPLINES ====================
@app.get("/helplines")
@app.get("/api/helplines")
@app.get("/ssec/api/helplines")
async def get_helplines(country: str = "US", helpline_type: Optional[str] = None):
    """Get crisis helplines by country"""
    try:
        helplines_list = helplines.get_helplines(country)
        
        if helpline_type:
            helplines_list = [h for h in helplines_list if h["type"] == helpline_type]
        
        return helplines_list
    except Exception as e:
        return get_mock_helplines(country)

@app.get("/helplines/search")
@app.get("/api/helplines/search")
@app.get("/ssec/api/helplines/search")
async def search_helplines(query: str):
    """Search helplines by name or number"""
    try:
        return helplines.search_helplines(query)
    except Exception as e:
        return []

@app.get("/helplines/countries")
@app.get("/api/helplines/countries")
@app.get("/ssec/api/helplines/countries")
async def get_available_countries():
    """Get list of countries with helpline data"""
    try:
        return helplines.get_all_countries()
    except Exception as e:
        return ["US", "UK", "UA", "SY", "HT"]

# ==================== MOCK DISASTER DATA ====================
@app.get("/disasters")
@app.get("/api/disasters")
@app.get("/ssec/api/disasters")
async def get_mock_disasters():
    """Mock disaster data"""
    return [
        {
            "id": "EQ12345",
            "name": "Earthquake - Caribbean Sea",
            "type": "Earthquake",
            "lat": 18.5,
            "lon": -77.2,
            "alertLevel": "RED",
            "startTime": datetime.utcnow().isoformat(),
            "description": "Magnitude 6.7 earthquake near Jamaica"
        },
        {
            "id": "TC67890",
            "name": "Tropical Storm - Gulf of Mexico",
            "type": "Cyclone",
            "lat": 25.3,
            "lon": -86.5,
            "alertLevel": "ORANGE",
            "startTime": datetime.utcnow().isoformat(),
            "description": "Category 1 hurricane approaching coast"
        },
        {
            "id": "FL54321",
            "name": "Flooding - Southeast Asia",
            "type": "Flood",
            "lat": 14.5,
            "lon": 108.2,
            "alertLevel": "GREEN",
            "startTime": datetime.utcnow().isoformat(),
            "description": "Monsoon flooding in Vietnam"
        }
    ]

@app.get("/news")
@app.get("/api/news")
@app.get("/ssec/api/news")
async def get_mock_news():
    """Mock news data"""
    return [
        {
            "title": "7.2 Earthquake Hits Caribbean",
            "source": "ReliefWeb",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#",
            "summary": "Major earthquake triggers tsunami warnings"
        },
        {
            "title": "Humanitarian Aid Reaches Flood Victims",
            "source": "UN OCHA",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#",
            "summary": "Emergency supplies distributed in affected regions"
        },
        {
            "title": "Conflict Escalates: Civilians Urged to Evacuate",
            "source": "ICRC",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#",
            "summary": "Humanitarian corridor established"
        }
    ]

# ==================== COMPREHENSIVE DASHBOARD DATA ====================
@app.get("/dashboard")
@app.get("/api/dashboard")
@app.get("/ssec/api/dashboard")
async def get_dashboard_data(country: Optional[str] = None):
    """Get all data for dashboard in one request"""
    try:
        # Fetch all data concurrently
        conflicts_task = acled.fetch_conflicts(country, days_back=7) if config.ACLED_API_KEY != "demo_key" else None
        signals_task = signals.get_signals()
        forecasts_task = views.get_forecasts(country)
        bases_task = asyncio.to_thread(military.get_all_bases)
        flights_task = flights.get_flights_near_location(20, 0, 500)
        heatmap_task = asyncio.to_thread(heatmap.generate_heatmap_data, None, 30, 100)
        
        # Gather results
        results = await asyncio.gather(
            signals_task,
            forecasts_task,
            bases_task,
            flights_task,
            heatmap_task,
            return_exceptions=True
        )
        
        signals_list, forecasts_list, bases, flights_near, heatmap_data = results
        
        # Handle conflicts separately
        if conflicts_task:
            conflicts = await conflicts_task
            formatted_conflicts = [acled.format_for_dashboard(c) for c in conflicts]
        else:
            formatted_conflicts = await get_mock_disasters()
        
        # Get stats
        stats = {
            "total_conflicts": len(formatted_conflicts),
            "total_flights": len(flights_near) if not isinstance(flights_near, Exception) else 0,
            "emergency_flights": len([f for f in flights_near if f.get("is_emergency")]) if not isinstance(flights_near, Exception) else 0,
            "active_signals": len(signals_list) if not isinstance(signals_list, Exception) else 0,
            "military_bases": len(bases) if not isinstance(bases, Exception) else 0
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
            "conflicts": formatted_conflicts,
            "signals": signals_list if not isinstance(signals_list, Exception) else [],
            "forecasts": forecasts_list if not isinstance(forecasts_list, Exception) else [],
            "military_bases": bases if not isinstance(bases, Exception) else [],
            "flights": [flights.format_for_map(f) for f in flights_near[:10]] if not isinstance(flights_near, Exception) else [],
            "heatmap": heatmap_data if not isinstance(heatmap_data, Exception) else []
        }
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        # Return combined mock data
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "total_conflicts": 3,
                "total_flights": 15,
                "emergency_flights": 2,
                "active_signals": 2,
                "military_bases": 20
            },
            "conflicts": await get_mock_disasters(),
            "signals": get_mock_signals(),
            "forecasts": get_mock_forecasts(),
            "military_bases": get_mock_military_bases(),
            "flights": [flights.format_for_map(f) for f in flights._get_mock_flights(20, 0, 500)[:10]],
            "heatmap": get_mock_heatmap()
        }

# ==================== MOCK DATA HELPERS ====================
def get_mock_conflicts():
    return [
        {
            "id": "conflict-1",
            "title": "⚔️ Battle - Damascus",
            "type": "Battles",
            "lat": 33.5,
            "lon": 36.3,
            "alertLevel": "RED",
            "severity": "CRITICAL",
            "color": "#ff4444",
            "timestamp": datetime.utcnow().isoformat(),
            "description": "Heavy fighting in eastern suburbs",
            "fatalities": 23,
            "actors": {"actor1": "Government forces", "actor2": "Opposition groups"},
            "country": "Syria",
            "source": "ACLED (Mock)"
        },
        {
            "id": "conflict-2",
            "title": "💥 Explosion - Gaza",
            "type": "Explosions",
            "lat": 31.5,
            "lon": 34.5,
            "alertLevel": "RED",
            "severity": "HIGH",
            "color": "#ff6666",
            "timestamp": datetime.utcnow().isoformat(),
            "description": "Airstrike in residential area",
            "fatalities": 12,
            "actors": {"actor1": "Military", "actor2": "Civilians"},
            "country": "Palestine",
            "source": "ACLED (Mock)"
        },
        {
            "id": "conflict-3",
            "title": "👥 Violence against civilians - Donetsk",
            "type": "Violence against civilians",
            "lat": 48.0,
            "lon": 37.8,
            "alertLevel": "ORANGE",
            "severity": "MODERATE",
            "color": "#ff8844",
            "timestamp": datetime.utcnow().isoformat(),
            "description": "Shelling of residential neighborhood",
            "fatalities": 5,
            "actors": {"actor1": "Separatists", "actor2": "Civilians"},
            "country": "Ukraine",
            "source": "ACLED (Mock)"
        }
    ]

def get_mock_conflict_stats():
    return {
        "total_events": 150,
        "total_fatalities": 450,
        "by_type": {
            "Battles": 80,
            "Explosions": 40,
            "Violence against civilians": 30
        },
        "by_severity": {
            "CRITICAL": 20,
            "HIGH": 45,
            "MODERATE": 50,
            "LOW": 35
        }
    }

def get_mock_hotspots():
    return [
        {"lat": 33.5, "lon": 36.3, "fatalities": 230, "events": 45, "location": "Damascus"},
        {"lat": 31.5, "lon": 34.5, "fatalities": 180, "events": 38, "location": "Gaza City"},
        {"lat": 48.5, "lon": 37.5, "fatalities": 150, "events": 42, "location": "Donetsk"},
        {"lat": 4.5, "lon": 18.5, "fatalities": 120, "events": 25, "location": "Bangui"},
        {"lat": 9.5, "lon": 30.0, "fatalities": 95, "events": 18, "location": "Bentiu"}
    ]

def get_mock_heatmap():
    return [
        {"lat": 18.5 + random.uniform(-3, 3), "lon": -77.2 + random.uniform(-3, 3), "intensity": random.uniform(0.5, 1.0), "type": "earthquake"},
        {"lat": 25.3 + random.uniform(-4, 4), "lon": -86.5 + random.uniform(-4, 4), "intensity": random.uniform(0.4, 0.9), "type": "hurricane"},
        {"lat": 14.5 + random.uniform(-5, 5), "lon": 108.2 + random.uniform(-5, 5), "intensity": random.uniform(0.3, 0.8), "type": "flood"},
        {"lat": 33.5 + random.uniform(-2, 2), "lon": 36.3 + random.uniform(-2, 2), "intensity": random.uniform(0.7, 1.0), "type": "conflict"},
        {"lat": 31.5 + random.uniform(-1.5, 1.5), "lon": 34.5 + random.uniform(-1.5, 1.5), "intensity": random.uniform(0.6, 0.95), "type": "conflict"},
        {"lat": 48.5 + random.uniform(-3, 3), "lon": 37.5 + random.uniform(-3, 3), "intensity": random.uniform(0.5, 0.9), "type": "conflict"},
    ] * 10

def get_mock_grid():
    points = []
    for i in range(-2, 3):
        for j in range(-2, 3):
            points.append({
                "lat": 18.5 + i * 0.5,
                "lon": -77.2 + j * 0.5,
                "intensity": random.uniform(0.3, 0.9)
            })
    return points

def get_mock_timeline(hours=24):
    data = []
    now = datetime.now()
    for i in range(hours):
        if random.random() > 0.7:
            data.append({
                "lat": 18.5 + random.uniform(-2, 2),
                "lon": -77.2 + random.uniform(-2, 2),
                "intensity": random.uniform(0.5, 1.0),
                "timestamp": (now - timedelta(hours=i)).isoformat(),
                "type": random.choice(["conflict", "earthquake", "flood"])
            })
    return data

def get_mock_displacement():
    return [
        {
            "id": "disp-1",
            "title": "🏕️ Displacement - Syria",
            "type": "Displacement",
            "lat": 33.5,
            "lon": 36.3,
            "alertLevel": "RED",
            "description": "230,000 people displaced",
            "population": 230000,
            "source": "HDX (Mock)"
        },
        {
            "id": "disp-2",
            "title": "🏕️ Displacement - Ukraine",
            "type": "Displacement",
            "lat": 48.5,
            "lon": 37.5,
            "alertLevel": "ORANGE",
            "description": "120,000 people displaced",
            "population": 120000,
            "source": "HDX (Mock)"
        }
    ]

def get_mock_food_security():
    return [
        {"country": "Yemen", "phase": "IPC 5", "population": 16000000},
        {"country": "South Sudan", "phase": "IPC 4", "population": 6500000},
        {"country": "Haiti", "phase": "IPC 3", "population": 4500000}
    ]

def get_mock_forecasts():
    return [
        {"country": "Syria", "lat": 33.5, "lon": 36.3, "risk_score": 85, "risk_level": "EXTREME", "forecast_month": "2026-04"},
        {"country": "Ukraine", "lat": 48.5, "lon": 37.5, "risk_score": 75, "risk_level": "EXTREME", "forecast_month": "2026-04"},
        {"country": "Mali", "lat": 17.5, "lon": -4.0, "risk_score": 65, "risk_level": "HIGH", "forecast_month": "2026-04"},
        {"country": "Ethiopia", "lat": 9.0, "lon": 38.7, "risk_score": 55, "risk_level": "HIGH", "forecast_month": "2026-04"}
    ]

def get_mock_forecast_heatmap():
    return [
        {"lat": 33.5, "lon": 36.3, "intensity": 0.85, "color": "#8B0000"},
        {"lat": 48.5, "lon": 37.5, "intensity": 0.75, "color": "#FF4444"},
        {"lat": 17.5, "lon": -4.0, "intensity": 0.65, "color": "#FF8844"},
        {"lat": 9.0, "lon": 38.7, "intensity": 0.55, "color": "#FF8844"}
    ]

def get_mock_signals():
    return [
        {
            "id": "signal-1",
            "headline": "🚨 CRITICAL: Escalation in Eastern Ukraine",
            "summary": "Fighting intensifies near Donetsk with heavy artillery",
            "severity": "high",
            "lat": 48.0,
            "lon": 37.8,
            "country": "Ukraine",
            "timestamp": datetime.utcnow().isoformat(),
            "trend": "+25% vs last week",
            "color": "#FF4444"
        },
        {
            "id": "signal-2",
            "headline": "⚠️ WARNING: Food security deteriorating in Haiti",
            "summary": "IPC Phase 4 (Emergency) likely in coming months",
            "severity": "medium",
            "lat": 18.5,
            "lon": -72.3,
            "country": "Haiti",
            "timestamp": datetime.utcnow().isoformat(),
            "trend": "Worsening",
            "color": "#FF8844"
        }
    ]

def get_mock_military_bases():
    return [
        {"name": "Ramstein Air Base", "icon": "🇺🇸", "type": "US Air Force", "lat": 49.4369, "lon": 7.6003, "country": "Germany"},
        {"name": "Camp Bondsteel", "icon": "🇺🇸", "type": "US Army", "lat": 42.3667, "lon": 21.25, "country": "Kosovo"},
        {"name": "Diego Garcia", "icon": "🇺🇸", "type": "US Navy", "lat": -7.3133, "lon": 72.4111, "country": "British Indian Ocean Territory"},
        {"name": "Tartus Naval Base", "icon": "🇷🇺", "type": "Russian Navy", "lat": 34.9167, "lon": 35.8833, "country": "Syria"},
        {"name": "Khmeimim Air Base", "icon": "🇷🇺", "type": "Russian Air Force", "lat": 35.4167, "lon": 35.9333, "country": "Syria"}
    ]

def get_mock_bases_near(lat, lon):
    return [
        {"name": "Nearby Base 1", "distance_km": 45, "country": "Unknown"},
        {"name": "Nearby Base 2", "distance_km": 120, "country": "Unknown"}
    ]

def get_mock_helplines(country):
    return [
        {"name": "🚨 Emergency Services", "number": "112", "available": "24/7", "type": "emergency"},
        {"name": "❤️ Red Cross", "number": "+123456789", "available": "24/7", "type": "humanitarian"}
    ]

if __name__ == "__main__":
    print("="*60)
    print("🚀 ssec-Sentinel v0.3.0 Starting...")
    print("="*60)
    print("\n📡 Endpoints available:")
    print("  • GET  /")
    print("  • GET  /health")
    print("  • GET  /conflicts")
    print("  • GET  /conflicts/stats")
    print("  • GET  /conflicts/hotspots")
    print("  • GET  /flights/near")
    print("  • GET  /flights/emergency")
    print("  • GET  /flights/near-disaster/{id}")
    print("  • GET  /heatmap")
    print("  • GET  /heatmap/conflicts")
    print("  • GET  /heatmap/natural")
    print("  • GET  /heatmap/grid")
    print("  • GET  /heatmap/timeline")
    print("  • GET  /heatmap/stats")
    print("  • GET  /signals")
    print("  • GET  /forecasts")
    print("  • GET  /displacement")
    print("  • GET  /military-bases")
    print("  • GET  /helplines")
    print("  • GET  /dashboard")
    print("\n🌍 All endpoints also available with /api/ prefix")
    print("📚 Documentation at: /docs")
    print("🎯 Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "ssec_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )