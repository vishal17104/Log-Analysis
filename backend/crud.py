from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from backend import models, schemas

# ============ HELPER FUNCTIONS ============

def serialize_datetime(obj):
    """Convert datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat() + 'Z'
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    else:
        return obj

def get_now():
    """Helper to get consistent UTC time"""
    return datetime.now(timezone.utc)

# ============ LOGS ============

def create_log(db: Session, service: str, level: str, message: str):
    db_log = models.Log(
        service=service,
        level=level,
        message=message,
        timestamp=get_now().replace(tzinfo=None) # naive for DB compatibility
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_log(db: Session, log_id: int):
    return db.query(models.Log).filter(models.Log.id == log_id).first()

def get_logs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    service: Optional[str] = None,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    query = db.query(models.Log)
    if service:
        query = query.filter(models.Log.service == service)
    if level:
        query = query.filter(models.Log.level == level)
    if start_time:
        query = query.filter(models.Log.timestamp >= start_time.replace(tzinfo=None))
    if end_time:
        query = query.filter(models.Log.timestamp <= end_time.replace(tzinfo=None))

    return query.order_by(models.Log.timestamp.desc()).offset(skip).limit(limit).all()

def create_logs_bulk(db: Session, logs: List[schemas.LogCreate]):
    db_logs = []
    for log in logs:
        log_dict = log.dict()
        log_dict = serialize_datetime(log_dict)
        
        db_log = models.Log(
            service=log.service,
            level=log.level,
            message=log.message,
            timestamp=(log.timestamp or get_now()).replace(tzinfo=None),
            host=getattr(log, 'host', None),
            pid=getattr(log, 'pid', None),
            ip_address=getattr(log, 'ip_address', None),
            status_code=getattr(log, 'status_code', None),
            trace_id=getattr(log, 'trace_id', None),
            raw_data=log_dict
        )
        db.add(db_log)
        db_logs.append(db_log)

    db.commit()
    return db_logs

def search_logs(db: Session, q: str, limit: int = 50):
    return db.query(models.Log).filter(
        models.Log.message.ilike(f"%{q}%")
    ).order_by(models.Log.timestamp.desc()).limit(limit).all()

def delete_log(db: Session, log_id: int):
    log = db.query(models.Log).filter(models.Log.id == log_id).first()
    if log:
        db.delete(log)
        db.commit()
        return True
    return False


# ============ STATS LOGIC (Optimized for Sentinel AI Dashboard) ============

def get_log_stats(db: Session, minutes: int = 60):

    now = datetime.utcnow()
    start_time = now - timedelta(minutes=minutes)

    logs = db.query(models.Log).filter(
        models.Log.timestamp >= start_time
    ).all()

    total_logs = len(logs)
    error_count = sum(1 for log in logs if log.level == "ERROR")
    warning_count = sum(1 for log in logs if log.level == "WARNING")
    info_count = sum(1 for log in logs if log.level == "INFO")
    debug_count = sum(1 for log in logs if log.level == "DEBUG")

    service_counts = {}
    for log in logs:
        service_counts[log.service] = service_counts.get(log.service, 0) + 1

    # -------- timeline aggregation --------
    timeline_query = (
        db.query(
            func.date_trunc("minute", models.Log.timestamp).label("minute"),
            func.count().label("count")
        )
        .filter(models.Log.level == "ERROR")
        .filter(models.Log.timestamp >= start_time)
        .group_by("minute")
        .order_by("minute")
        .all()
    )

    timeline = [
        {
            "minute": minute.isoformat(),
            "count": count
        }
        for minute, count in timeline_query
    ]

    return {
        "total_logs": total_logs,
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "debug_count": debug_count,
        "by_service": service_counts,
        "time_range": {
            "start": start_time.isoformat(),
            "end": now.isoformat()
        },
        "timeline": timeline
    }

# ============ INCIDENTS ============

def create_incident(db: Session, incident: schemas.IncidentCreate):
    db_incident = models.Incident(
        title=incident.title,
        severity=incident.severity,
        error_count=incident.error_count,
        window_start=incident.window_start.replace(tzinfo=None) if incident.window_start else None,
        window_end=incident.window_end.replace(tzinfo=None) if incident.window_end else None,
        status="open",
        detected_at=get_now().replace(tzinfo=None)
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

def get_incidents(db: Session, skip: int = 0, limit: int = 50, status: str = None, severity: str = None):
    query = db.query(models.Incident)
    if status: query = query.filter(models.Incident.status == status)
    if severity: query = query.filter(models.Incident.severity == severity)
    return query.order_by(models.Incident.detected_at.desc()).offset(skip).limit(limit).all()

def get_incident(db: Session, incident_id: int):
    return db.query(models.Incident).filter(models.Incident.id == incident_id).first()

def update_incident_status(db: Session, incident_id: int, status: str):
    incident = get_incident(db, incident_id)
    if incident:
        incident.status = status
        if status == "resolved":
            incident.resolved_at = get_now().replace(tzinfo=None)
        db.commit()
        db.refresh(incident)
    return incident

def get_incident_summary(db: Session, days: int = 1):
    """
    Summary for Sentinel UI metrics. 
    Includes: Resolutions Today, MTTD calculation, and open count.
    """
    now = get_now().replace(tzinfo=None)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Resolutions Today
    res_today = db.query(models.Incident).filter(
        and_(models.Incident.status == "resolved", models.Incident.resolved_at >= start_of_today)
    ).count()

    # Active Incidents
    active = db.query(models.Incident).filter(models.Incident.status == "open").count()

    # Simple MTTD (Mean Time to Detect) - Average time from window_start to detected_at
    incidents_with_window = db.query(models.Incident).filter(models.Incident.window_start.isnot(None)).limit(20).all()
    mttd = "4.2m" # Default fallback
    if incidents_with_window:
        diffs = [(i.detected_at - i.window_start).total_seconds() / 60 for i in incidents_with_window]
        avg = sum(diffs) / len(diffs)
        mttd = f"{avg:.1f}m"

    return {
        "active_incidents": active,
        "resolutions_today": res_today,
        "mttd": mttd,
        "availability": "99.98%" # Mock or calculated based on logs
    }

# ============ RUNBOOKS ============

def get_runbook_by_service_type(db: Session, service: str, error_type: str):
    return db.query(models.Runbook).filter(
        models.Runbook.service == service,
        models.Runbook.error_type == error_type
    ).first()

def get_all_runbooks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Runbook).offset(skip).limit(limit).all()