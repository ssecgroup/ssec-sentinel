"""ssec-Sentinel Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys (get from https://developer.acleddata.com)
    ACLED_API_KEY = os.getenv("ACLED_API_KEY", "")
    ACLED_EMAIL = os.getenv("ACLED_EMAIL", "")
    
    # HDX API (free, no key needed)
    HDX_BASE_URL = "https://hapi.humdata.org/api/v1"
    
    # Cache settings
    CACHE_TTL = 300  # 5 minutes
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Update intervals (seconds)
    CONFLICT_UPDATE_INTERVAL = 3600  # 1 hour
    SIGNAL_UPDATE_INTERVAL = 300     # 5 minutes
    FORECAST_UPDATE_INTERVAL = 86400 # 24 hours
    
config = Config()
