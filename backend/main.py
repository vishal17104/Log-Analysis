from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import (
    logs,
    incidents,
    runbooks,
    agent_router,
    recommendation_router,
    log_stream,  # NEW (WebSocket router)
)

from backend.database import engine
from backend import models

from backend.services.log_processor import start_processor  # NEW

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Log Analyzer")

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

# Include WebSocket router
app.include_router(log_stream.router)  # NEW


# Start background log processor
@app.on_event("startup")
async def startup_event():
    await start_processor()


@app.get("/")
def root():
    return {
        "message": "Agentic Log Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "logs": "/logs",
            "incidents": "/incidents",
            "runbooks": "/runbooks",
            "agent": "/agent",
            "recommendations": "/recommendations",
            "websocket_logs": "/ws/logs",  # NEW
            "docs": "/docs"
        },
    }