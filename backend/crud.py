from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from backend import models
from typing import Optional, List
from backend import schemas

#creating log
def create_log(db: Session, service: str, level: str, message: str):
    db_log = models.Log(
        service=service,
        level=level,
        message=message,
        timestamp=datetime.utcnow()
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

#getting logs
def get_logs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    service: Optional[str] = None,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """Get logs with filters"""
    query = db.query(models.Log)
    if service:
        query = query.filter(models.Log.service == service)
    if level:
        query = query.filter(models.Log.level == level)
    if start_time:
        query = query.filter(models.Log.timestamp >= start_time)
    if end_time:
        query = query.filter(models.Log.timestamp <= end_time)

    return query.order_by(
    models.Log.timestamp.desc()
).offset(skip).limit(limit).all()


def get_log(db: Session, log_id: int):
    """Get a log by ID"""
    return db.query(models.Log).filter(models.Log.id == log_id).first()


def get_log_stats(db: Session, minutes: int = 60):
    """Get log statistics for last N minutes"""
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)

    level_counts = db.query(models.Log.level, func.count().label('count')).filter(models.Log.timestamp >= cutoff).group_by(models.Log.level).all()

    service_counts = db.query(models.Log.service, func.count().label('count')).filter(models.Log.timestamp >= cutoff).group_by(models.Log.service).all()

    timeline = db.query(func.date_trunc('minute', models.Log.timestamp).label('minute'), func.count().label('count')).filter(models.Log.level == 'ERROR',models.Log.timestamp >= cutoff).group_by('minute').order_by('minute').all()

    return {
        "total_logs": sum(c for _, c in level_counts),
        "error_count": next((c for l, c in level_counts if l == 'ERROR'), 0),
        "warn_count": next((c for l, c in level_counts if l == 'WARN'), 0),
        "info_count": next((c for l, c in level_counts if l == 'INFO'), 0),
        "debug_count": next((c for l, c in level_counts if l == 'DEBUG'), 0),
        "by_service": {s: c for s, c in service_counts},
        "timeline": [{"minute": m, "count": c} for m, c in timeline],
        "time_range": {
            "start": cutoff,
            "end": datetime.utcnow()
        }
    }

def search_logs(db: Session, q: str, limit: int = 50):
    """Search logs by message"""
    return db.query(models.Log).filter(
        models.Log.message.ilike(f"%{q}%")
    ).order_by(
        models.Log.timestamp.desc()
    ).limit(limit).all()

def delete_log(db: Session, log_id: int):
    """Delete a log by ID"""
    log = db.query(models.Log).filter(models.Log.id == log_id).first()
    if log:
        db.delete(log)
        db.commit()
        return True
    return False


def create_logs_bulk(db: Session, logs: List[schemas.LogCreate]):
    """Create multiple logs in bulk"""
    db_logs = []
    for log in logs:
        db_log = models.Log(
            service=log.service,
            level=log.level,
            message=log.message,
            timestamp=log.timestamp or datetime.utcnow(),
            host=log.host,
            pid=log.pid,
            ip_address=log.ip_address,
            status_code=log.status_code,
            raw_data=log.dict()
        )
        db.add(db_log)
        db_logs.append(db_log)

    db.commit()
    for log in db_logs:
        db.refresh(log)
    return db_logs



 