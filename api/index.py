from fastapi import FastAPI
from mangum import Mangum
import httpx

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "ssec-sentinel-frontend"}

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"https://ssec-sentinel.onrender.com/{path}")
            return response.json()
        except:
            return {"error": "Backend unavailable"}

handler = Mangum(app)
