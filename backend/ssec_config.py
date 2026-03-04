"""ssec-Sentinel Configuration"""
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Configuration class for ssec-Sentinel"""
    
    # ACLED OAuth credentials
    ACLED_USERNAME = os.getenv("ACLED_USERNAME", "")
    ACLED_PASSWORD = os.getenv("ACLED_PASSWORD", "")
    
    # HDX API (free, no key needed)
    HDX_BASE_URL = "https://hapi.humdata.org/api/v1"
    
    # Cache settings
    CACHE_TTL = 300  # 5 minutes
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

config = Config()