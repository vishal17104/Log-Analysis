from fastapi import FastAPI
from backend.routers import logs, incidents

app = FastAPI(
    title="Log Analysis API",
    description="Ingestion and analysis API for system logs",
    version="1.0.0"
)

app.include_router(logs.router)
app.include_router(incidents.router)


