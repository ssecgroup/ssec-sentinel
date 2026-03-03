from fastapi import FastAPI
from mangum import Mangum
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

# Create FastAPI app
app = FastAPI(title="ssec-Sentinel API")

@app.get("/")
async def root():
    return {
        "message": "ssec-Sentinel API",
        "version": "0.3.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ssec-sentinel",
        "timestamp": "2026-03-04T00:00:00Z"
    }

# Import your actual endpoints if possible
try:
    from backend.ssec_app import app as fastapi_app
    app = fastapi_app
    print("✅ Loaded full application")
except ImportError as e:
    print(f"⚠️ Using minimal app: {e}")

# Handler for Vercel
handler = Mangum(app)

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
