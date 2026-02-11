from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import models
from backend import crud
from backend import schemas
from backend.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Log Analyzer")

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
            "POST /logs": "Create a log",
            "GET /logs": "Get recent logs"
        }
    }

@app.post("/logs", response_model=schemas.LogResponse)
def create_log(log: schemas.LogCreate, db: Session = Depends(get_db)):
    return crud.create_log(db = db, service=log.service, level=log.level, message=log.message)

@app.get("/logs", response_model=List[schemas.LogResponse])
def get_logs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get recent logs"""
    return crud.get_logs(db, skip=skip, limit=limit)
