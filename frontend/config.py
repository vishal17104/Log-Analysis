# frontend/config.py
import os
from pathlib import Path

# API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = BACKEND_URL  

# App Configuration
APP_TITLE = os.getenv("APP_TITLE", "Sentinel AI")
APP_ICON = os.getenv("APP_ICON", "🤖")
PAGE_TITLE = os.getenv("PAGE_TITLE", "Sentinel AI Monitoring")
LAYOUT = os.getenv("LAYOUT", "wide")

# Refresh settings
AUTO_REFRESH_INTERVAL = int(os.getenv("AUTO_REFRESH_INTERVAL", "5000"))  
ENABLE_AUTO_REFRESH = os.getenv("ENABLE_AUTO_REFRESH", "true").lower() == "true"

# Theme
THEME = os.getenv("THEME", "dark")
PRIMARY_COLOR = os.getenv("PRIMARY_COLOR", "#00d1ff")
BACKGROUND_COLOR = os.getenv("BACKGROUND_COLOR", "#0e1117")
CARD_COLOR = os.getenv("CARD_COLOR", "#1e2130")

# Paths
BASE_DIR = Path(__file__).resolve().parent