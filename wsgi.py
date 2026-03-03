import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

# Import the FastAPI app
from backend.ssec_app import app

# This is for gunicorn to find
application = app
