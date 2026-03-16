import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine
from backend import models

from backend.services.log_processor import start_processor
from backend.services.log_broadcaster import start_broadcaster

# Routers
from backend.routers import (
    logs,
    incidents,
    runbooks,
    agent_router,
    recommendation_router,
    log_stream,
    notifications,
    ws_logs,
    analytics
)
from backend.logging_config import setup_logging

# Agent runtime state
import backend.routers.agent_router as agent_runtime


# ---------------- LOGGER ---------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
setup_logging()
logger = logging.getLogger("sentinel-api")


# ---------------- DATABASE INIT ---------------- #

models.Base.metadata.create_all(bind=engine)


# ---------------- APP INIT ---------------- #

app = FastAPI(
    title="Sentinel AI - Agentic Log Analyzer",
    version="1.0.0",
    description="AI-powered log monitoring, incident detection and automated remediation platform."
)


# ---------------- CORS ---------------- #

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- API ROUTERS ---------------- #

app.include_router(logs.router)
app.include_router(incidents.router)
app.include_router(runbooks.router)

app.include_router(agent_router.router)
app.include_router(recommendation_router.router)
app.include_router(notifications.router)

app.include_router(analytics.router)

# WebSockets
app.include_router(log_stream.router)
app.include_router(ws_logs.router)


# ---------------- STARTUP SERVICES ---------------- #

@app.on_event("startup")
async def startup_event():

    try:

        await start_processor()
        logger.info("Log processor started")

        await start_broadcaster()
        logger.info("Log broadcaster started")

        agent_runtime.agent_running = True
        logger.info("Agent runtime started")

    except Exception as e:
        logger.error(f"Startup error: {e}")


# ---------------- HEALTH CHECK ---------------- #

@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------------- ROOT ---------------- #

@app.get("/")
def root():

    return {
        "service": "Sentinel AI - Agentic Log Analyzer",
        "version": "1.0.0",
        "status": {
            "logs": "active",
            "agent": "running"
        },
        "endpoints": {
            "logs": "/logs",
            "incidents": "/incidents",
            "runbooks": "/runbooks",
            "agent": "/agent",
            "recommendations": "/recommendations",
            "analytics": "/logs/stats",
            "websocket_logs": "/ws/logs",
            "docs": "/docs"
        }
    }