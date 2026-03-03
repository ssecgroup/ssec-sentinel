from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "ssec-Sentinel API", "version": "0.3.0"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "ssec-sentinel"}

handler = Mangum(app)
