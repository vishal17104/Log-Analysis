from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from backend import models, crud, schemas
from backend.database import SessionLocal, engine
from routers import logs


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Log Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "Log Analyzer API",
         "endpoints": {
            "POST /logs": "Create logs",
            "GET /logs": "Get logs with filters",
            "GET /logs/stats": "Get statistics",
            "GET /logs/search": "Search logs",
            "GET /logs/{id}": "Get log by ID",
            "DELETE /logs/{id}": "Delete log"
         }
    }