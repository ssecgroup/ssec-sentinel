from fastapi import FastAPI
from mangum import Mangum

app = FastAPI(title="ssec-Sentinel API")

@app.get("/")
async def root():
    return {
        "message": "ssec-Sentinel API",
        "version": "0.3.0",
        "status": "operational"
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "ssec-sentinel"
    }

@app.get("/api/conflicts")
async def get_conflicts():
    return [
        {
            "id": "conflict-1",
            "title": "⚔️ Conflict - Example",
            "lat": 33.5,
            "lon": 36.3,
            "severity": "HIGH",
            "fatalities": 23
        }
    ]

handler = Mangum(app)
