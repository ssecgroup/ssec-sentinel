from fastapi import FastAPI, Request
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ssec-proxy")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RENDER_BACKEND = "https://ssec-sentinel.onrender.com"

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "ssec-sentinel-proxy"}

@app.get("/api/debug")
async def debug():
    return {"message": "Proxy working", "backend": RENDER_BACKEND}

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    query = str(request.query_params)
    url = f"{RENDER_BACKEND}/{path}"
    if query:
        url += f"?{query}"
    
    logger.info(f"Proxying to: {url}")
    
    body = None
    if request.method in ["POST", "PUT"]:
        body = await request.body()
    
    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                follow_redirects=True
            )
            return response.json()
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return {"error": "Backend unavailable"}

handler = Mangum(app)
