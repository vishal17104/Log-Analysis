from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import schemas, crud
from backend.database import get_db
import detector

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("/", response_model=List[schemas.IncidentResponse])
def read_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all incidents with filters"""

    incidents = crud.get_incidents(
        db,
        skip=skip,
        limit=limit,
        status=status,
        severity=severity
    )
    return incidents

@router.get("/{incident_id}", response_model=schemas.IncidentDetailResponse)
def read_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed incident info including logs"""

    incident = crud.get_detailed_incidents(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.patch("/{incident_id/status}", response_model=schemas.IncidentResponse)
def update_incident_status(
    incident_id: int,
    status_update: schemas.IncidentStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update incident status"""

    incident = crud.update_incident_status(db, incident_id, status_update.status)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.post("/{incident_id}/resolve", response_model=schemas.IncidentResponse)
def resolve_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """Mark incident as resolved"""

    incident = crud.update_incident_status(db, incident_id, "resolved")
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.post("/trigger-detection")
def trigger_detection(
    db : Session = Depends(get_db)
):
    """Manually trigger incident detection"""

    try:
        detector.detect_and_create_incidents(db)
        return {"message": "Detection triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    
@router.get("/stats/summary", response_model=schemas.IncidentSummary)  
def get_incident_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get incident statistics for last N days"""
    summary = crud.get_incident_summary(db, days)
    return summary