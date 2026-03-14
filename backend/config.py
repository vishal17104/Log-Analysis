import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

#BASE PATHS
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

#DATABASE
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")

#API KEYS
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set. AI features will fail.")

#BACKEND URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

#DETECTOR CONFIG
ERROR_THRESHOLD = int(os.getenv("ERROR_THRESHOLD", "2"))
TIME_WINDOW = int(os.getenv("TIME_WINDOW", "10"))
CONSECUTIVE_TIME = int(os.getenv("CONSECUTIVE_TIME", "2"))

#SEVERITY THRESHOLDS
SEVERITY_THRESHOLDS = {
    "CRITICAL": int(os.getenv("SEVERITY_CRITICAL", "50")),
    "HIGH": int(os.getenv("SEVERITY_HIGH", "20")),
    "MEDIUM": int(os.getenv("SEVERITY_MEDIUM", "10")),
    "LOW": int(os.getenv("SEVERITY_LOW", "5"))
}

#LOGGING
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "app.log")

#ENVIRONMENT
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_DOCKER = os.getenv("IS_DOCKER", "false").lower() == "true"