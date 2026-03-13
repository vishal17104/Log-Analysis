import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine
from backend import models

from backend.services.log_processor import start_processor
from backend.services.log_broadcaster import start_broadcaster

from backend.routers import (
    logs,
    incidents,
    runbooks,
    agent_router,
    recommendation_router,
    log_stream,
    notifications,
    ws_logs
)

# Import agent runtime state
import backend.routers.agent_router as agent_runtime

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Log Analyzer")

logger = logging.getLogger(__name__)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routers
app.include_router(logs.router)
app.include_router(incidents.router)
app.include_router(runbooks.router)
app.include_router(agent_router.router)
app.include_router(recommendation_router.router)
app.include_router(notifications.router)

# Include WebSocket routers
app.include_router(log_stream.router)
app.include_router(ws_logs.router)


# ---------------- STARTUP SERVICES ---------------- #

@app.on_event("startup")
async def startup_event():

    # Start log ingestion services
    await start_processor()
    await start_broadcaster()

    # Start agent runtime
    agent_runtime.agent_running = True

    logger.info("Log processor and broadcaster started")
    logger.info("Agent runtime started")


# ---------------- ROOT ENDPOINT ---------------- #

@app.get("/")
def root():
    return {
        "message": "Agentic Log Analyzer API",
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
            "websocket_logs": "/ws/logs",
            "docs": "/docs"
        },
    }