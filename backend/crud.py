from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from backend import models
from typing import Optional, List
from backend import schemas

# Helper function to serialize datetime objects
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
        "warning_count": next((c for l, c in level_counts if l == 'WARN'), 0),
        "info_count": next((c for l, c in level_counts if l == 'INFO'), 0),
        "debug_count": next((c for l, c in level_counts if l == 'DEBUG'), 0),
        "by_service": {s: c for s, c in service_counts},
        "timeline": [{"minute": m.isoformat() + 'Z' if hasattr(m, 'isoformat') else m, "count": c} for m, c in timeline],
        "time_range": {
            "start": cutoff.isoformat() + 'Z',
            "end": datetime.utcnow().isoformat() + 'Z'
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
    """Create multiple logs in bulk with proper datetime serialization"""
    db_logs = []
    for log in logs:
        # Convert log to dict and serialize all datetime objects
        log_dict = log.dict()
        log_dict = serialize_datetime(log_dict)
        
        db_log = models.Log(
            service=log.service,
            level=log.level,
            message=log.message,
            timestamp=log.timestamp or datetime.utcnow(),
            host=getattr(log, 'host', None),
            pid=getattr(log, 'pid', None),
            ip_address=getattr(log, 'ip_address', None),
            status_code=getattr(log, 'status_code', None),
            raw_data=log_dict  # Now with all datetime converted to strings
        )
        db.add(db_log)
        db_logs.append(db_log)

    db.commit()
    for log in db_logs:
        db.refresh(log)
    return db_logs


def create_incident(db: Session, incident: schemas.IncidentCreate):
    """Create an incident"""
    db_incident = models.Incident(
        title=incident.title,
        severity=incident.severity,
        error_count=incident.error_count,
        window_start=incident.window_start,
        window_end=incident.window_end,
        status="open"
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

def get_incidents(
    db: Session, 
    skip: int = 0, 
    limit: int = 50,
    status: Optional[str] = None,
    severity: Optional[str] = None
):
    """Get incidents with filters"""
    query = db.query(models.Incident)
    
    if status:
        query = query.filter(models.Incident.status == status)
    if severity:
        query = query.filter(models.Incident.severity == severity)
    
    return query.order_by(
        models.Incident.detected_at.desc()
    ).offset(skip).limit(limit).all()

def get_incident(db: Session, incident_id: int):
    """Get single incident by ID"""
    return db.query(models.Incident).filter(
        models.Incident.id == incident_id
    ).first()

def get_detailed_incidents(db: Session, incident_id: int):
    """Get detailed incident info including logs"""
    incident = get_incident(db, incident_id)
    if not incident:
        return None

    # Get logs from the incident's time window
    if incident.window_start and incident.window_end:
        logs = db.query(models.Log).filter(
            models.Log.timestamp >= incident.window_start,
            models.Log.timestamp <= incident.window_end,
            models.Log.level == 'ERROR'
        ).order_by(models.Log.timestamp).all()
    else:
        logs = []

    # Convert incident to dict and add logs
    incident_dict = {
        "id": incident.id,
        "title": incident.title,
        "severity": incident.severity,
        "status": incident.status,
        "error_count": incident.error_count,
        "detected_at": incident.detected_at.isoformat() + 'Z' if incident.detected_at else None,
        "resolved_at": incident.resolved_at.isoformat() + 'Z' if incident.resolved_at else None,
        "window_start": incident.window_start.isoformat() + 'Z' if incident.window_start else None,
        "window_end": incident.window_end.isoformat() + 'Z' if incident.window_end else None,
        "logs": [
            {
                "id": log.id, 
                "message": log.message, 
                "timestamp": log.timestamp.isoformat() + 'Z' if log.timestamp else None
            } 
            for log in logs
        ]
    }

    return incident_dict

def update_incident_status(db: Session, incident_id: int, status: str):
    """Update incident status"""
    incident = get_incident(db, incident_id)
    if incident:
        incident.status = status
        if status == "resolved":
            incident.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(incident)
    return incident

def get_incident_summary(db: Session, days: int = 7):
    """Get incident statistics"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Total incidents
    total = db.query(models.Incident).filter(
        models.Incident.detected_at >= cutoff
    ).count()

    # Open incidents
    open_count = db.query(models.Incident).filter(
        models.Incident.detected_at >= cutoff,
        models.Incident.status == "open"
    ).count()

    # By severity
    severity_counts = db.query(
        models.Incident.severity,
        func.count().label('count')
    ).filter(
        models.Incident.detected_at >= cutoff
    ).group_by(
        models.Incident.severity
    ).all()

    # Average resolution time for resolved incidents
    resolved = db.query(models.Incident).filter(
        models.Incident.detected_at >= cutoff,
        models.Incident.status == "resolved",
        models.Incident.resolved_at.isnot(None)
    ).all()

    if resolved:
        total_time = sum(
            (inc.resolved_at - inc.detected_at).total_seconds() / 60
            for inc in resolved
        )
        avg_time = total_time / len(resolved)
    else:
        avg_time = None

    return {
        "total_incidents": total,
        "open_incidents": open_count,
        "resolved_incidents": total - open_count,
        "by_severity": {s: c for s, c in severity_counts},
        "avg_resolution_time": avg_time
    }