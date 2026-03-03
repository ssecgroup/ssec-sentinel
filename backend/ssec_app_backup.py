"""ssec-Sentinel Main Application - COMPLETE VERSION"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio

# Add path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import all collectors
from collectors.ssec_acled import ACLEDCollector
from collectors.ssec_hdx import HDXCollector
from collectors.ssec_views import VIEWSCollector
from collectors.ssec_signals import HDXSignalsCollector
from collectors.ssec_military import MilitaryBasesCollector
from collectors.ssec_helplines_enhanced import EnhancedHelplinesCollector
from ssec_config import config

# Initialize collectors
acled = ACLEDCollector(config.ACLED_API_KEY, config.ACLED_EMAIL)
hdx = HDXCollector()
views = VIEWSCollector()
signals = HDXSignalsCollector()
military = MilitaryBasesCollector()
helplines = EnhancedHelplinesCollector()

# Create FastAPI app
app = FastAPI(
    title="ssec-Sentinel API",
    description="Emergency Intelligence Platform with War Zone Monitoring",
    version="0.2.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HEALTH CHECK ====================
@app.get("/ssec/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.2.0",
        "service": "ssec-sentinel",
        "collectors": {
            "acled": bool(config.ACLED_API_KEY),
            "hdx": True,
            "views": True,
            "signals": True,
            "military": True
        }
    }

# ==================== CONFLICT ENDPOINTS ====================
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ssec/api/conflicts/stats")
async def get_conflict_stats(country: Optional[str] = None):
    """Get conflict statistics"""
    try:
        stats = await acled.get_conflict_stats(country)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HDX HUMANITARIAN DATA ====================
@app.get("/ssec/api/displacement")
async def get_displacement(country: Optional[str] = None):
    """Get displacement data from HDX"""
    try:
        data = await hdx.get_displacement(country)
        return [hdx.format_alert(d) for d in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ssec/api/food-security")
async def get_food_security(country: Optional[str] = None):
    """Get food security data"""
    try:
        return await hdx.get_food_security(country)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VIEWS FORECASTS ====================
@app.get("/ssec/api/forecasts")
async def get_forecasts(country: Optional[str] = None):
    """Get conflict risk forecasts"""
    try:
        forecasts = await views.get_forecasts(country)
        return forecasts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ssec/api/forecasts/heatmap")
async def get_forecast_heatmap():
    """Get forecast data formatted for heatmap"""
    try:
        forecasts = await views.get_forecasts()
        heatmap = [{
            "lat": f["lat"],
            "lon": f["lon"],
            "intensity": f["risk_score"] / 100,
            "color": views.get_risk_color(f["risk_score"])
        } for f in forecasts if f["lat"] and f["lon"]]
        return heatmap
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HDX SIGNALS ====================
@app.get("/ssec/api/signals")
async def get_signals(severity: Optional[str] = None):
    """Get automated crisis alerts"""
    try:
        alerts = await signals.get_signals(severity)
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ssec/api/signals/check")
async def check_new_signals(background_tasks: BackgroundTasks):
    """Check for new alerts since last check"""
    try:
        last_check = datetime.utcnow() - timedelta(minutes=5)
        new_alerts = await signals.check_for_new_alerts(last_check)
        
        # Could trigger notifications here
        if new_alerts:
            background_tasks.add_task(notify_new_alerts, new_alerts)
        
        return {
            "new_alerts": len(new_alerts),
            "alerts": new_alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def notify_new_alerts(alerts):
    """Send notifications for new alerts (implement as needed)"""
    print(f"New alerts: {len(alerts)}")

# ==================== MILITARY BASES ====================
@app.get("/ssec/api/military-bases")
async def get_military_bases(country: Optional[str] = None):
    """Get military installations"""
    try:
        if country:
            return military.get_bases_by_country(country)
        return military.get_all_bases()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ssec/api/military-bases/near")
async def get_bases_near_conflict(lat: float, lon: float, radius: float = 500):
    """Find military bases near conflict zone"""
    try:
        return military.get_bases_near_conflict(lat, lon, radius)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENHANCED HELPLINES ====================
@app.get("/ssec/api/helplines")
async def get_helplines(country: str = "US", helpline_type: Optional[str] = None):
    """Get crisis helplines by country"""
    try:
        helplines_list = helplines.get_helplines(country)
        
        if helpline_type:
            helplines_list = [h for h in helplines_list if h["type"] == helpline_type]
        
        return helplines_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ssec/api/helplines/search")
async def search_helplines(query: str):
    """Search helplines by name or number"""
    try:
        return helplines.search_helplines(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ssec/api/helplines/countries")
async def get_available_countries():
    """Get list of countries with helpline data"""
    try:
        return helplines.get_all_countries()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== COMPREHENSIVE DASHBOARD DATA ====================
@app.get("/ssec/api/dashboard")
async def get_dashboard_data(country: Optional[str] = None):
    """Get all data for dashboard in one request"""
    try:
        # Fetch all data concurrently
        conflicts_task = acled.fetch_conflicts(country, days_back=7)
        signals_task = signals.get_signals()
        forecasts_task = views.get_forecasts(country)
        bases_task = asyncio.to_thread(military.get_all_bases)
        
        conflicts, signals_list, forecasts_list, bases = await asyncio.gather(
            conflicts_task,
            signals_task,
            forecasts_task,
            bases_task
        )
        
        # Format conflicts
        formatted_conflicts = [acled.format_for_dashboard(c) for c in conflicts]
        
        # Get stats
        stats = {
            "total_conflicts": len(conflicts),
            "total_fatalities": sum(int(c.get("fatalities", 0)) for c in conflicts),
            "active_signals": len(signals_list),
            "military_bases": len(bases)
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
            "conflicts": formatted_conflicts,
            "signals": signals_list,
            "forecasts": forecasts_list,
            "military_bases": bases
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MOCK DATA (Fallback) ====================
@app.get("/ssec/api/disasters")
async def get_mock_disasters():
    """Fallback mock disaster data"""
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
        }
    ]

@app.get("/ssec/api/news")
async def get_mock_news():
    """Fallback mock news data"""
    return [
        {
            "title": "7.2 Earthquake Hits Caribbean",
            "source": "ReliefWeb",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#"
        },
        {
            "title": "Humanitarian Aid Reaches Flood Victims",
            "source": "UN OCHA",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#"
        }
    ]

@app.get("/ssec/api/heatmap")
async def get_mock_heatmap():
    """Fallback mock heatmap data"""
    import random
    return [
        {"lat": 18.0 + random.uniform(-3, 3),
         "lon": -77.0 + random.uniform(-3, 3),
         "intensity": random.uniform(0.5, 1.0)}
        for _ in range(50)
    ]

if __name__ == "__main__":
    print("="*50)
    print("🚀 ssec-Sentinel v0.2.0 Starting...")
    print("="*50)
    print("\n📡 Endpoints available:")
    print("  • GET  /ssec/health")
    print("  • GET  /ssec/api/conflicts")
    print("  • GET  /ssec/api/conflicts/stats")
    print("  • GET  /ssec/api/conflicts/hotspots")
    print("  • GET  /ssec/api/signals")
    print("  • GET  /ssec/api/forecasts")
    print("  • GET  /ssec/api/displacement")
    print("  • GET  /ssec/api/military-bases")
    print("  • GET  /ssec/api/helplines")
    print("  • GET  /ssec/api/dashboard")
    print("\n🌍 Dashboard ready at: http://localhost:8000/ssec/api/dashboard")
    print("🎯 Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "ssec_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
