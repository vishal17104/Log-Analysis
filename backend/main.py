from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import logs, incidents, runbooks, agent_router, recommendation_router
from backend.database import engine
from backend import models

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

# Include all routers
app.include_router(logs.router)
app.include_router(incidents.router)
app.include_router(runbooks.router)
app.include_router(agent_router.router)
app.include_router(recommendation_router.router)  # NEW

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
            "recommendations": "/recommendations",  # NEW
            "docs": "/docs"
        }
    }