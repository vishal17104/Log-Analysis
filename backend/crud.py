from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, List

from backend import models, schemas


# ---------------- HELPER ---------------- #

def serialize_datetime(obj):
    """Convert datetime objects to ISO strings for JSON storage"""
    if isinstance(obj, datetime):
        return obj.isoformat() + "Z"
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(v) for v in obj]
    return obj


# ---------------- LOGS ---------------- #

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


def create_logs_bulk(db: Session, logs: List[schemas.LogCreate]):

    db_logs = []

    for log in logs:
        log_dict = serialize_datetime(log.dict())

        db_log = models.Log(
            service=log.service,
            level=log.level,
            message=log.message,
            timestamp=log.timestamp or datetime.utcnow(),
            host=getattr(log, "host", None),
            pid=getattr(log, "pid", None),
            ip_address=getattr(log, "ip_address", None),
            status_code=getattr(log, "status_code", None),
            trace_id=getattr(log, "trace_id", None),
            raw_data=log_dict
        )

        db.add(db_log)
        db_logs.append(db_log)

    db.commit()

    for log in db_logs:
        db.refresh(log)

    return db_logs


def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    service: Optional[str] = None,
    level: Optional[str] = None
):

    query = db.query(models.Log)

    if service:
        query = query.filter(models.Log.service == service)

    if level:
        query = query.filter(models.Log.level == level)

    return query.order_by(
        models.Log.timestamp.desc()
    ).offset(skip).limit(limit).all()


def get_log(db: Session, log_id: int):
    return db.query(models.Log).filter(
        models.Log.id == log_id
    ).first()


# ---------------- INCIDENTS ---------------- #

def create_incident(db: Session, incident: schemas.IncidentCreate):

    db_incident = models.Incident(
        title=incident.title,
        service=incident.service,
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

    query = db.query(models.Incident)

    if status:
        query = query.filter(models.Incident.status == status)

    if severity:
        query = query.filter(models.Incident.severity == severity)

    return query.order_by(
        models.Incident.detected_at.desc()
    ).offset(skip).limit(limit).all()


def get_incident(db: Session, incident_id: int):
    return db.query(models.Incident).filter(
        models.Incident.id == incident_id
    ).first()


def update_incident_status(db: Session, incident_id: int, status: str):

    incident = get_incident(db, incident_id)

    if incident:
        incident.status = status

        if status == "resolved":
            incident.resolved_at = datetime.utcnow()

        db.commit()
        db.refresh(incident)

    return incident


# ---------------- INCIDENT ANALYTICS ---------------- #

def get_incident_summary(db: Session, days: int = 7):

    cutoff = datetime.utcnow() - timedelta(days=days)

    total = db.query(models.Incident).filter(
        models.Incident.detected_at >= cutoff
    ).count()

    open_count = db.query(models.Incident).filter(
        models.Incident.detected_at >= cutoff,
        models.Incident.status == "open"
    ).count()

    severity_counts = db.query(
        models.Incident.severity,
        func.count()
    ).group_by(models.Incident.severity).all()

    return {
        "total_incidents": total,
        "open_incidents": open_count,
        "resolved_incidents": total - open_count,
        "by_severity": {s: c for s, c in severity_counts}
    }


# ---------------- RUNBOOKS ---------------- #

def get_all_runbooks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Runbook).offset(skip).limit(limit).all()


def get_runbook_by_name(db: Session, name: str):
    return db.query(models.Runbook).filter(
        models.Runbook.name == name
    ).first()


def create_runbook(
    db: Session,
    name: str,
    content: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None
):

    db_runbook = models.Runbook(
        name=name,
        title=title or name.replace("_", " ").replace(".md", "").title(),
        content=content,
        tags=tags or []
    )

    db.add(db_runbook)
    db.commit()
    db.refresh(db_runbook)

    return db_runbook


def get_runbook_by_service_type(db: Session, service: str, error_type: str):

    return db.query(models.Runbook).filter(
        models.Runbook.service == service,
        models.Runbook.error_type == error_type
    ).first()


def create_runbook_by_service(
    db: Session,
    service: str,
    error_type: str,
    content: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    name: Optional[str] = None
):

    if not name:
        name = f"{service}_{error_type}.md"

    db_runbook = models.Runbook(
        service=service,
        error_type=error_type,
        name=name,
        title=title,
        content=content,
        tags=tags or []
    )

    db.add(db_runbook)
    db.commit()
    db.refresh(db_runbook)

    return db_runbook