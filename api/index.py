from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "ssec-Sentinel API"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

handler = Mangum(app)
