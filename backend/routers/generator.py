# backend/routers/generator.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from backend.database import get_db
from backend.services.mock_generator import generate_log_batch, insert_logs_batch
import detector

router = APIRouter(prefix="/generate", tags=["Log Generator"])

class GenerateRequest(BaseModel):
    batch_size: int = 100
    error_burst: bool = False
    auto_detect: bool = True
    service: Optional[str] = None

@router.post("/logs")
def generate_logs(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate and insert mock logs directly into database.
    This bypasses the API for better performance.
    """
    
    # Validate batch size
    if request.batch_size < 1 or request.batch_size > 1000:
        raise HTTPException(status_code=400, detail="Batch size must be between 1 and 1000")
    
    # Generate logs
    logs = generate_log_batch(
        batch_size=request.batch_size,
        error_burst=request.error_burst
    )
    
    # Filter by service if specified
    if request.service:
        logs = [log for log in logs if log["service"] == request.service]
    
    # Insert directly into database
    count = insert_logs_batch(db, logs)
    
    # Run detection in background (doesn't block response)
    if request.auto_detect:
        background_tasks.add_task(detector.detect_and_create_incidents, db)
    
    return {
        "message": f"Generated and inserted {count} logs",
        "batch_size": request.batch_size,
        "error_burst": request.error_burst,
        "service_filter": request.service,
        "auto_detect_triggered": request.auto_detect
    }

@router.post("/error-burst")
def generate_error_burst(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Quick one-click error burst (100 logs, 80% errors)"""
    
    logs = generate_log_batch(batch_size=100, error_burst=True)
    count = insert_logs_batch(db, logs)
    
    background_tasks.add_task(detector.detect_and_create_incidents, db)
    
    return {
        "message": f"🔥 Error burst generated! {count} logs inserted (80% errors)",
        "logs_inserted": count
    }

@router.post("/normal-traffic")
def generate_normal_traffic(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate normal traffic (50 logs, normal error rate)"""
    
    logs = generate_log_batch(batch_size=50, error_burst=False)
    count = insert_logs_batch(db, logs)
    
    background_tasks.add_task(detector.detect_and_create_incidents, db)
    
    return {
        "message": f"📊 Normal traffic generated! {count} logs inserted",
        "logs_inserted": count
    }