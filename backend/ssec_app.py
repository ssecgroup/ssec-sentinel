from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="ssec-Sentinel API", version="0.3.0")

@app.get("/")
async def root():
    return {
        "message": "ssec-Sentinel API",
        "version": "0.3.0",
        "status": "operational",
        "endpoints": [
            "/",
            "/health",
            "/api/health",
            "/conflicts",
            "/flights/near",
            "/heatmap",
            "/signals",
            "/military-bases",
            "/helplines"
        ]
    }

@app.get("/health")
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "ssec-sentinel",
        "timestamp": datetime.utcnow().isoformat()
    }

# Your existing endpoints here...
# (keep all your existing @app.get endpoints)

# Add this at the end to catch all routes
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    return {
        "error": "Endpoint not found",
        "path": full_path,
        "message": f"Route '/{full_path}' does not exist. Try /health or /docs"
    }
