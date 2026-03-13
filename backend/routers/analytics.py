from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any, List

from backend.database import get_db
from backend import models


router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ---------------- SUMMARY METRICS ---------------- #

@router.get("/summary")
def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:

    cutoff = datetime.utcnow() - timedelta(days=days)

    total_incidents = db.query(models.Incident).filter(
        models.Incident.detected_at >= cutoff
    ).count()

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
        avg_mttr = total_time / len(resolved)
    else:
        avg_mttr = None

    resolved_count = len(resolved)
    success_rate = (resolved_count / total_incidents * 100) if total_incidents > 0 else 0

    incidents_with_runbook = db.query(models.Incident).join(
        models.IncidentReasoning,
        models.Incident.id == models.IncidentReasoning.incident_id
    ).filter(
        models.Incident.detected_at >= cutoff,
        models.IncidentReasoning.suggested_runbook.isnot(None)
    ).count()

    runbook_usage = (incidents_with_runbook / total_incidents * 100) if total_incidents > 0 else 0

    return {
        "total_incidents": total_incidents,
        "avg_mttr_minutes": round(avg_mttr, 1) if avg_mttr else None,
        "success_rate": round(success_rate, 1),
        "runbook_usage_rate": round(runbook_usage, 1),
        "period_days": days
    }


# ---------------- INCIDENT TIMELINE ---------------- #

@router.get("/incidents-timeline")
def get_incidents_timeline(
    days: int = Query(30, ge=1, le=365),
    interval: str = Query("day", pattern="^(hour|day|week)$"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:

    cutoff = datetime.utcnow() - timedelta(days=days)

    if interval == "hour":
        trunc = func.date_trunc("hour", models.Incident.detected_at)
    elif interval == "day":
        trunc = func.date_trunc("day", models.Incident.detected_at)
    else:
        trunc = func.date_trunc("week", models.Incident.detected_at)

    results = db.query(
        trunc.label("period"),
        func.count().label("count")
    ).filter(
        models.Incident.detected_at >= cutoff
    ).group_by("period").order_by("period").all()

    return [
        {"period": r[0].isoformat(), "count": r[1]}
        for r in results
    ]


# ---------------- SEVERITY BREAKDOWN ---------------- #

@router.get("/severity-breakdown")
def get_severity_breakdown(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, int]:

    cutoff = datetime.utcnow() - timedelta(days=days)

    results = db.query(
        models.Incident.severity,
        func.count().label("count")
    ).filter(
        models.Incident.detected_at >= cutoff
    ).group_by(models.Incident.severity).all()

    return {sev: count for sev, count in results}


# ---------------- TOP SERVICES ---------------- #

@router.get("/top-services")
def get_top_services(
    days: int = Query(30, ge=1, le=365),
    limit: int = 5,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:

    cutoff = datetime.utcnow() - timedelta(days=days)

    results = db.query(
        models.Incident.title,
        func.count().label("count")
    ).filter(
        models.Incident.detected_at >= cutoff
    ).group_by(models.Incident.title).order_by(
        func.count().desc()
    ).limit(limit).all()

    services = []

    for title, count in results:

        if "in" in title:
            service = title.split("in ")[-1].split()[0]
        else:
            service = "unknown"

        services.append({
            "service": service,
            "count": count
        })

    return services


# ---------------- AGENT PERFORMANCE ---------------- #

@router.get("/agent-performance")
def get_agent_performance(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:

    cutoff = datetime.utcnow() - timedelta(days=days)

    feedback = db.query(models.Feedback).filter(
        models.Feedback.created_at >= cutoff
    ).all()

    if not feedback:
        return {
            "decision_accuracy": 0,
            "runbook_match_rate": 0,
            "total_decisions": 0
        }

    total_decisions = len(feedback)

    correct = sum(
        1 for f in feedback
        if f.human_decision == "accepted"
    )

    decision_accuracy = correct / total_decisions * 100

    incidents_with_runbook = db.query(models.IncidentReasoning).filter(
        models.IncidentReasoning.created_at >= cutoff,
        models.IncidentReasoning.suggested_runbook.isnot(None)
    ).count()

    total_incidents = db.query(models.Incident).filter(
        models.Incident.detected_at >= cutoff
    ).count()

    runbook_match_rate = (
        incidents_with_runbook / total_incidents * 100
        if total_incidents > 0 else 0
    )

    return {
        "decision_accuracy": round(decision_accuracy, 1),
        "runbook_match_rate": round(runbook_match_rate, 1),
        "total_decisions": total_decisions,
        "period_days": days
    }


# ---------------- RUNBOOK HEATMAP ---------------- #

@router.get("/runbook-usage-heatmap")
def get_runbook_usage_heatmap(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:

    cutoff = datetime.utcnow() - timedelta(days=days)

    results = db.query(
        models.IncidentReasoning.suggested_runbook,
        func.count().label("count")
    ).filter(
        models.IncidentReasoning.created_at >= cutoff,
        models.IncidentReasoning.suggested_runbook.isnot(None)
    ).group_by(
        models.IncidentReasoning.suggested_runbook
    ).order_by(
        func.count().desc()
    ).limit(10).all()

    return [
        {"runbook": r[0], "usage_count": r[1]}
        for r in results
    ]