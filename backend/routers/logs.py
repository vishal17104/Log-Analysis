from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from backend import schemas, crud
from backend.database import get_db

router = APIRouter(prefix="/logs", tags=["Logs"])

# 1️⃣ CREATE (Bulk)
@router.post("/", response_model=List[schemas.LogResponse])
def create_logs(
    logs: List[schemas.LogCreate],
    db: Session = Depends(get_db)
):
    """Bulk create logs (used by mock_data generator)"""
    return crud.create_logs_bulk(db, logs)

# 2️⃣ READ ALL (with Filters)
@router.get("/", response_model=List[schemas.LogResponse])
def read_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: Optional[str] = None,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    return crud.get_logs(
        db=db,
        skip=skip,
        limit=limit,
        service=service,
        level=level,
        start_time=start_time,
        end_time=end_time
    )

# 3️⃣ STATS (Static path must be ABOVE {log_id})
@router.get("/stats", response_model=schemas.LogStats)
def get_log_stats(
    minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db)
):
    """Get log distribution and counts for the dashboard"""
    return crud.get_log_stats(db, minutes)

# 4️⃣ SEARCH (Static path must be ABOVE {log_id})
@router.get("/search", response_model=List[schemas.LogResponse])
def search_logs(
    q: str = Query(..., min_length=2, description="Search term for log messages"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Text search inside log messages"""
    return crud.search_logs(db, q, limit)

# 5️⃣ READ ONE (Dynamic path)
@router.get("/{log_id}", response_model=schemas.LogResponse)
def read_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    log = crud.get_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

# 6️⃣ DELETE (Dynamic path)
@router.delete("/{log_id}")
def delete_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    deleted = crud.delete_log(db, log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"message": "Log deleted successfully"}