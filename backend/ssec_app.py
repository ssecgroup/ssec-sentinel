"""ssec-Sentinel Main Application - Fixed Version"""
import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
import random
import traceback

# Setup logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

try:
    logger.info("Starting ssec-Sentinel...")
    
    # Add path
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.append(str(backend_dir))
    logger.info(f"Added {backend_dir} to path")
    
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, Response
    import uvicorn
    
    logger.info("Imported core modules")
    
    # Import collectors with error handling
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
            
            # Initialize with config params if needed
            if config_params:
                from ssec_config import config
                args = [getattr(config, param) for param in config_params]
                collectors[class_name] = collector_class(*args)
            else:
                collectors[class_name] = collector_class()
                
            logger.info(f"✓ Imported and initialized {class_name}")
        except Exception as e:
            logger.error(f"Failed to import {class_name}: {e}")
            collectors[class_name] = None
    
    from ssec_config import config
    logger.info("Imported config")
    
    # Assign collectors to variables for backward compatibility
    acled = collectors.get("ACLEDCollector")
    hdx = collectors.get("HDXCollector")
    views = collectors.get("VIEWSCollector")
    signals = collectors.get("HDXSignalsCollector")
    military = collectors.get("MilitaryBasesCollector")
    helplines = collectors.get("EnhancedHelplinesCollector")
    flights = collectors.get("FlightCollector")
    heatmap = collectors.get("HeatmapCollector")
    
    # Check which collectors are available
    available_collectors = {name: collector is not None for name, collector in collectors.items()}
    logger.info(f"Available collectors: {available_collectors}")
    
    # Create FastAPI app
    app = FastAPI(
        title="ssec-Sentinel API",
        description="Emergency Intelligence Platform with War Zone Monitoring",
        version="0.3.0",
    )
    logger.info("✓ FastAPI app created")
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("✓ CORS configured")
    
except Exception as e:
    logger.error(f"FATAL: Failed to start application: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

# ==================== ROOT ENDPOINT ====================
@app.get("/")
@app.get("/api")
@app.get("/ssec")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ssec-Sentinel API",
        "version": "0.3.0",
        "status": "operational",
        "collectors": {name: "available" if status else "unavailable" 
                      for name, status in available_collectors.items()},
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
            "/dashboard",
            "/api/dashboard",
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
        "collectors": available_collectors
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
    if acled and available_collectors["ACLEDCollector"]:
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
            logger.error(f"Error fetching conflicts: {e}")
            return get_mock_conflicts()
    else:
        return get_mock_conflicts()

@app.get("/conflicts/stats")
@app.get("/api/conflicts/stats")
@app.get("/ssec/api/conflicts/stats")
async def get_conflict_stats(country: Optional[str] = None):
    """Get conflict statistics"""
    if acled and available_collectors["ACLEDCollector"]:
        try:
            stats = await acled.get_conflict_stats(country)
            return stats
        except Exception as e:
            logger.error(f"Error fetching conflict stats: {e}")
            return get_mock_conflict_stats()
    else:
        return get_mock_conflict_stats()

@app.get("/conflicts/hotspots")
@app.get("/api/conflicts/hotspots")
@app.get("/ssec/api/conflicts/hotspots")
async def get_hotspots(threshold: int = 10):
    """Get conflict hotspots (areas with most fatalities)"""
    if acled and available_collectors["ACLEDCollector"]:
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
            logger.error(f"Error fetching hotspots: {e}")
            return get_mock_hotspots()
    else:
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
    if flights and available_collectors["FlightCollector"]:
        try:
            flights_near = await flights.get_flights_near_location(lat, lon, radius)
            
            if emergency_only:
                flights_near = [f for f in flights_near if f.get("is_emergency")]
            
            formatted = [flights.format_for_map(f) for f in flights_near]
            return formatted
        except Exception as e:
            logger.error(f"Error fetching flights: {e}")
            return flights._get_mock_flights(lat, lon, radius) if flights else get_mock_flights(lat, lon, radius)
    else:
        return get_mock_flights(lat, lon, radius)

@app.get("/flights/emergency")
@app.get("/api/flights/emergency")
@app.get("/ssec/api/flights/emergency")
async def get_emergency_flights():
    """Get all flights with emergency squawk codes"""
    if flights and available_collectors["FlightCollector"]:
        try:
            emergency = await flights.get_emergency_flights()
            return [flights.format_for_map(f) for f in emergency]
        except Exception as e:
            logger.error(f"Error fetching emergency flights: {e}")
            mocks = flights._get_mock_flights(20, 0, 500) if flights else get_mock_flights(20, 0, 500)
            return [flights.format_for_map(f) for f in mocks if f.get("is_emergency")] if flights else mocks
    else:
        return [f for f in get_mock_flights(20, 0, 500) if f.get("is_emergency")]

@app.get("/flights/near-disaster/{disaster_id}")
@app.get("/api/flights/near-disaster/{disaster_id}")
@app.get("/ssec/api/flights/near-disaster/{disaster_id}")
async def get_flights_near_disaster(disaster_id: str, radius: float = 100):
    """Get flights near a specific disaster"""
    if flights and available_collectors["FlightCollector"]:
        try:
            flights_near = flights._get_mock_flights(18.5, -77.2, radius)
        except:
            flights_near = get_mock_flights(18.5, -77.2, radius)
    else:
        flights_near = get_mock_flights(18.5, -77.2, radius)
    
    return {
        "disaster_id": disaster_id,
        "aircraft_count": len(flights_near),
        "aircraft": flights_near
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
            data = heatmap.generate_heatmap_data(
                disaster_type=disaster_type,
                days=days,
                points=points
            )
            return data
        except Exception as e:
            logger.error(f"Error generating heatmap: {e}")
            return get_mock_heatmap()
    else:
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
    else:
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
    else:
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
    else:
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
    else:
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
    else:
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
    else:
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
    else:
        return get_mock_food_security()

# ==================== VIEWS FORECASTS ====================
@app.get("/forecasts")
@app.get("/api/forecasts")
@app.get("/ssec/api/forecasts")
async def get_forecasts(country: Optional[str] = None):
    """Get conflict risk forecasts"""
    if views and available_collectors["VIEWSCollector"]:
        try:
            forecasts = await views.get_forecasts(country)
            return forecasts
        except Exception as e:
            logger.error(f"Error fetching forecasts: {e}")
            return get_mock_forecasts()
    else:
        return get_mock_forecasts()

@app.get("/forecasts/heatmap")
@app.get("/api/forecasts/heatmap")
@app.get("/ssec/api/forecasts/heatmap")
async def get_forecast_heatmap():
    """Get forecast data formatted for heatmap"""
    if views and available_collectors["VIEWSCollector"]:
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
            logger.error(f"Error generating forecast heatmap: {e}")
            return get_mock_forecast_heatmap()
    else:
        return get_mock_forecast_heatmap()

# ==================== HDX SIGNALS ====================
@app.get("/signals")
@app.get("/api/signals")
@app.get("/ssec/api/signals")
async def get_signals(severity: Optional[str] = None):
    """Get automated crisis alerts"""
    if signals and available_collectors["HDXSignalsCollector"]:
        try:
            alerts = await signals.get_signals(severity)
            return alerts
        except Exception as e:
            logger.error(f"Error fetching signals: {e}")
            return get_mock_signals()
    else:
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
            
            return {
                "new_alerts": len(new_alerts),
                "alerts": new_alerts
            }
        except Exception as e:
            logger.error(f"Error checking new signals: {e}")
            return {"new_alerts": 0, "alerts": []}
    else:
        return {"new_alerts": 0, "alerts": []}

async def notify_new_alerts(alerts):
    """Send notifications for new alerts"""
    logger.info(f"New alerts: {len(alerts)}")

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
    else:
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
            logger.error(f"Error fetching nearby bases: {e}")
            return get_mock_bases_near(lat, lon)
    else:
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
    else:
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
    else:
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
            return ["US", "UK", "UA", "SY", "HT"]
    else:
        return ["US", "UK", "UA", "SY", "HT"]

# ==================== MOCK DISASTER DATA ====================
@app.get("/disasters")
@app.get("/api/disasters")
@app.get("/ssec/api/disasters")
async def get_mock_disasters_endpoint():
    """Mock disaster data"""
    return get_mock_disasters()

@app.get("/news")
@app.get("/api/news")
@app.get("/ssec/api/news")
async def get_mock_news_endpoint():
    """Mock news data"""
    return get_mock_news()

# ==================== COMPREHENSIVE DASHBOARD DATA ====================
@app.get("/dashboard")
@app.get("/api/dashboard")
@app.get("/ssec/api/dashboard")
async def get_dashboard_data(country: Optional[str] = None):
    """Get all data for dashboard in one request"""
    try:
        # Fetch all data concurrently
        tasks = []
        
        # Conflicts
        if acled and available_collectors["ACLEDCollector"] and config.ACLED_API_KEY != "demo_key":
            tasks.append(acled.fetch_conflicts(country, days_back=7))
        else:
            tasks.append(get_mock_conflicts())
        
        # Signals
        if signals and available_collectors["HDXSignalsCollector"]:
            tasks.append(signals.get_signals())
        else:
            tasks.append(get_mock_signals())
        
        # Forecasts
        if views and available_collectors["VIEWSCollector"]:
            tasks.append(views.get_forecasts(country))
        else:
            tasks.append(get_mock_forecasts())
        
        # Bases
        if military and available_collectors["MilitaryBasesCollector"]:
            tasks.append(asyncio.to_thread(military.get_all_bases))
        else:
            tasks.append(get_mock_military_bases())
        
        # Flights
        if flights and available_collectors["FlightCollector"]:
            tasks.append(flights.get_flights_near_location(20, 0, 500))
        else:
            tasks.append(get_mock_flights(20, 0, 500))
        
        # Heatmap
        if heatmap and available_collectors["HeatmapCollector"]:
            tasks.append(asyncio.to_thread(heatmap.generate_heatmap_data, None, 30, 100))
        else:
            tasks.append(get_mock_heatmap())
        
        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results
        conflicts_result, signals_result, forecasts_result, bases_result, flights_result, heatmap_result = results
        
        # Handle exceptions
        formatted_conflicts = conflicts_result if not isinstance(conflicts_result, Exception) else get_mock_conflicts()
        signals_list = signals_result if not isinstance(signals_result, Exception) else get_mock_signals()
        forecasts_list = forecasts_result if not isinstance(forecasts_result, Exception) else get_mock_forecasts()
        bases = bases_result if not isinstance(bases_result, Exception) else get_mock_military_bases()
        flights_near = flights_result if not isinstance(flights_result, Exception) else get_mock_flights(20, 0, 500)
        heatmap_data = heatmap_result if not isinstance(heatmap_result, Exception) else get_mock_heatmap()
        
        # Get stats
        stats = {
            "total_conflicts": len(formatted_conflicts),
            "total_flights": len(flights_near),
            "emergency_flights": len([f for f in flights_near if f.get("is_emergency", False)]),
            "active_signals": len(signals_list),
            "military_bases": len(bases)
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
            "conflicts": formatted_conflicts,
            "signals": signals_list,
            "forecasts": forecasts_list,
            "military_bases": bases,
            "flights": flights_near[:10] if len(flights_near) > 10 else flights_near,
            "heatmap": heatmap_data
        }
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
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
            "conflicts": get_mock_conflicts(),
            "signals": get_mock_signals(),
            "forecasts": get_mock_forecasts(),
            "military_bases": get_mock_military_bases(),
            "flights": get_mock_flights(20, 0, 500)[:10],
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
    points = []
    base_points = [
        (18.5, -77.2, "earthquake"),
        (25.3, -86.5, "hurricane"),
        (14.5, 108.2, "flood"),
        (33.5, 36.3, "conflict"),
        (31.5, 34.5, "conflict"),
        (48.5, 37.5, "conflict"),
    ]
    
    for lat, lon, type_name in base_points:
        for _ in range(10):
            points.append({
                "lat": lat + random.uniform(-3, 3),
                "lon": lon + random.uniform(-3, 3),
                "intensity": random.uniform(0.5, 1.0),
                "type": type_name
            })
    return points

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

def get_mock_heatmap_stats():
    return {
        "total_points": 500,
        "by_type": {"conflict": 300, "earthquake": 100, "flood": 100},
        "avg_intensity": 0.75,
        "max_intensity": 0.95,
        "min_intensity": 0.3,
        "active_zones": 12
    }

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
        {"name": "Nearby Base 1", "distance_km": 45, "country": "Unknown", "lat": lat + 0.5, "lon": lon + 0.5},
        {"name": "Nearby Base 2", "distance_km": 120, "country": "Unknown", "lat": lat - 0.8, "lon": lon + 1.2}
    ]

def get_mock_helplines(country):
    return [
        {"name": "🚨 Emergency Services", "number": "112", "available": "24/7", "type": "emergency", "country": country},
        {"name": "❤️ Red Cross", "number": "+123456789", "available": "24/7", "type": "humanitarian", "country": country}
    ]

def get_mock_flights(lat, lon, radius):
    flights_list = []
    for i in range(15):
        is_emergency = random.random() > 0.8
        flights_list.append({
            "id": f"flight-{i}",
            "callsign": f"CALL{i:03d}",
            "lat": lat + random.uniform(-radius/100, radius/100),
            "lon": lon + random.uniform(-radius/100, radius/100),
            "altitude": random.randint(3000, 40000),
            "speed": random.randint(200, 500),
            "heading": random.randint(0, 359),
            "is_emergency": is_emergency,
            "squawk": "7700" if is_emergency else random.choice(["1200", "2000", "3000"]),
            "aircraft_type": random.choice(["B738", "A320", "C172", "B77W", "E190"])
        })
    return flights_list

def get_mock_disasters():
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

def get_mock_news():
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

if __name__ == "__main__":
    print("="*60)
    print("🚀 ssec-Sentinel v0.3.0 Starting...")
    print("="*60)
    print("\n📡 Available collectors:")
    for name, available in available_collectors.items():
        status = "✅" if available else "❌"
        print(f"  {status} {name}")
    
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
        "__main__:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )