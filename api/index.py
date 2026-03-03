from fastapi import FastAPI
from mangum import Mangum
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

# Import your main app
from backend.ssec_app import app as fastapi_app

# Create a new app for Vercel/Render
app = FastAPI(title="ssec-Sentinel API", version="0.3.0")

# Include your main app's routes
app.mount("/api", fastapi_app)

# Add health check at root
@app.get("/")
async def root():
    return {
        "message": "ssec-Sentinel API",
        "version": "0.3.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Handler for serverless
handler = Mangum(app)
