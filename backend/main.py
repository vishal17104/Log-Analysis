from fastapi import FastAPI
from backend.routers import logs

app = FastAPI(
    title="Log Analysis API",
    description="Ingestion and analysis API for system logs",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"status": "Log Analysis API running"}

app.include_router(logs.router)
