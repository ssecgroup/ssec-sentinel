from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
import random
from datetime import datetime

app = FastAPI(title="ssec-Sentinel API", version="0.3.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data generators
def generate_conflicts():
    return [
        {
            "id": "1",
            "title": "⚔️ Conflict - Damascus",
            "type": "Battles",
            "lat": 33.5,
            "lon": 36.3,
            "severity": "HIGH",
            "fatalities": random.randint(10, 30),
            "country": "Syria",
            "color": "#ff4444",
            "description": "Heavy fighting in eastern suburbs"
        },
        {
            "id": "2",
            "title": "💥 Conflict - Gaza",
            "type": "Explosions",
            "lat": 31.5,
            "lon": 34.5,
            "severity": "HIGH",
            "fatalities": random.randint(5, 20),
            "country": "Palestine",
            "color": "#ff4444",
            "description": "Airstrikes in residential area"
        },
        {
            "id": "3",
            "title": "🔥 Conflict - Donetsk",
            "type": "Battles",
            "lat": 48.0,
            "lon": 37.8,
            "severity": "MEDIUM",
            "fatalities": random.randint(1, 10),
            "country": "Ukraine",
            "color": "#ff8844",
            "description": "Artillery duels along front line"
        }
    ]

def generate_flights(lat=None, lon=None):
    flights = []
    centers = [
        (33.5, 36.3), (31.5, 34.5), (48.0, 37.8),
        (49.4, 7.6), (42.3, 21.2), (34.9, 35.8)
    ]
    
    if lat and lon:
        centers = [(lat, lon)]
    
    for center in centers:
        for i in range(random.randint(1, 3)):
            is_emergency = random.random() < 0.2
            flights.append({
                "callsign": random.choice(["DAL", "UAL", "AAL", "JBU", "SWA"]) + str(random.randint(100, 999)),
                "lat": center[0] + random.uniform(-1, 1),
                "lon": center[1] + random.uniform(-1, 1),
                "altitude": random.randint(25000, 41000),
                "speed": random.randint(400, 550),
                "is_emergency": is_emergency,
                "squawk": "7700" if is_emergency else "1200"
            })
    return flights

@app.get("/")
async def root():
    return {
        "message": "ssec-Sentinel API",
        "version": "0.3.0",
        "status": "operational",
        "endpoints": [
            "/api/health",
            "/api/conflicts",
            "/api/flights/near",
            "/api/heatmap",
            "/api/signals",
            "/api/military-bases"
        ]
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "ssec-sentinel",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.3.0"
    }

@app.get("/api/conflicts")
async def get_conflicts():
    return generate_conflicts()

@app.get("/api/flights/near")
async def get_flights_near(lat: float = 20.0, lon: float = 0.0, radius: float = 500):
    return generate_flights(lat, lon)

@app.get("/api/heatmap")
async def get_heatmap():
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

@app.get("/api/signals")
async def get_signals():
    return [
        {
            "headline": "🚨 CRITICAL: Escalation in Eastern Ukraine",
            "severity": "high",
            "summary": "Fighting intensifies near Donetsk with heavy artillery",
            "trend": "+25% vs last week"
        },
        {
            "headline": "⚠️ WARNING: Food security deteriorating in Haiti",
            "severity": "medium",
            "summary": "IPC Phase 4 (Emergency) likely in coming months",
            "trend": "Worsening"
        }
    ]

@app.get("/api/military-bases")
async def get_military_bases():
    return [
        {"name": "Ramstein Air Base", "icon": "🇺🇸", "lat": 49.4369, "lon": 7.6003, "country": "Germany"},
        {"name": "Camp Bondsteel", "icon": "🇺🇸", "lat": 42.3667, "lon": 21.25, "country": "Kosovo"},
        {"name": "Tartus Naval Base", "icon": "🇷🇺", "lat": 34.9167, "lon": 35.8833, "country": "Syria"},
        {"name": "Khmeimim Air Base", "icon": "🇷🇺", "lat": 35.4167, "lon": 35.9333, "country": "Syria"}
    ]

handler = Mangum(app)
