from fastapi import FastAPI
from mangum import Mangum
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

# Import your existing app
try:
    from backend.ssec_app import app as fastapi_app
except ImportError:
    # Fallback if import fails
    from fastapi import FastAPI
    fastapi_app = FastAPI()
    
    @fastapi_app.get("/")
    async def root():
        return {"message": "ssec-Sentinel API"}

# Create Mangum handler for Vercel
handler = Mangum(fastapi_app)

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
