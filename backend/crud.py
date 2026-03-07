from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from backend import models, schemas

# --- LOGS ---

def get_log(db: Session, log_id: int):
    return db.query(models.Log).filter(models.Log.id == log_id).first()

def get_logs(db: Session, skip: int, limit: int, service=None, level=None, start_time=None, end_time=None):
    query = db.query(models.Log)
    if service:
        query = query.filter(models.Log.service == service)
    if level:
        query = query.filter(models.Log.level == level)
    if start_time:
        query = query.filter(models.Log.timestamp >= start_time)
    if end_time:
        query = query.filter(models.Log.timestamp <= end_time)
    
    return query.order_by(models.Log.timestamp.desc()).offset(skip).limit(limit).all()

def create_logs_bulk(db: Session, logs: List[schemas.LogCreate]):
    db_logs = [models.Log(**log.model_dump()) for log in logs]
    db.add_all(db_logs)
    db.commit()
    # No refresh on bulk for performance; logs will have IDs after commit
    return db_logs

def search_logs(db: Session, query_str: str, limit: int):
    return db.query(models.Log).filter(
        models.Log.message.ilike(f"%{query_str}%")
    ).limit(limit).all()

def delete_log(db: Session, log_id: int):
    log = db.query(models.Log).filter(models.Log.id == log_id).first()
    if log:
        db.delete(log)
        db.commit()
        return True
    return False

# --- STATS LOGIC ---

def get_log_stats(db: Session, minutes: int):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    # Counts by Level
    levels = db.query(models.Log.level, func.count(models.Log.id)).filter(
        models.Log.timestamp >= cutoff
    ).group_by(models.Log.level).all()
    level_map = {lvl: count for lvl, count in levels}

    # Counts by Service
    services = db.query(models.Log.service, func.count(models.Log.id)).filter(
        models.Log.timestamp >= cutoff
    ).group_by(models.Log.service).all()
    
    # Total count
    total = db.query(models.Log).filter(models.Log.timestamp >= cutoff).count()

    return {
        "total_logs": total,
        "error_count": level_map.get("ERROR", 0),
        "warning_count": level_map.get("WARNING", 0),
        "info_count": level_map.get("INFO", 0),
        "debug_count": level_map.get("DEBUG", 0),
        "by_service": {svc: count for svc, count in services},
        "time_range": {"start": cutoff, "end": datetime.now(timezone.utc)},
        "timeline": [] # You can expand this for graphing later
    }