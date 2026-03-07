from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import time
import logging

from backend import models
from backend.database import SessionLocal
from backend.services.incident_service import (
    create_incident_from_spike,
    get_open_incident_for_service
)
from backend.services.notifier import notifier
from backend.services.pattern_matcher import get_pattern_matcher  # 👈 NEW IMPORT

# ---------------- CONFIG ---------------- #

ERROR_THRESHOLD = 2              # errors per minute
TIME_WINDOW = 10                  # minutes to look back
CONSECUTIVE_TIME = 2              # sustained minutes required

SEVERITY_THRESHOLDS = {
    "CRITICAL": 50,
    "HIGH": 20,
    "MEDIUM": 10,
    "LOW": 5
}

# ---------------- LOGGING ---------------- #

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- DETECTION LOGIC ---------------- #

def check_error_rate(db: Session) -> List[Dict[str, Any]]:
    """
    Check error rates per service within TIME_WINDOW
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=TIME_WINDOW)

    error_counts = (
        db.query(
            models.Log.service,
            func.count().label("error_count")
        )
        .filter(
            models.Log.level == "ERROR",
            models.Log.timestamp >= cutoff
        )
        .group_by(models.Log.service)
        .all()
    )

    results = []

    for service, count in error_counts:
        if count >= ERROR_THRESHOLD:
            severity = "LOW"
            for level, threshold in SEVERITY_THRESHOLDS.items():
                if count >= threshold:
                    severity = level

            results.append({
                "service": service,
                "error_count": count,
                "severity": severity,
                "window_start": cutoff,
                "window_end": datetime.now(timezone.utc)
            })

            logger.info(
                f"High errors in {service}: {count} errors/min ({severity})"
            )

    return results


def check_consecutive_spikes(db: Session, service: str) -> bool:
    """
    Check if service has exceeded ERROR_THRESHOLD
    for CONSECUTIVE_TIME consecutive minutes
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=CONSECUTIVE_TIME)

    minute_buckets = (
        db.query(
            func.date_trunc("minute", models.Log.timestamp).label("minute"),
            func.count().label("count")
        )
        .filter(
            models.Log.service == service,
            models.Log.level == "ERROR",
            models.Log.timestamp >= cutoff
        )
        .group_by("minute")
        .order_by("minute")
        .all()
    )

    if len(minute_buckets) < CONSECUTIVE_TIME:
        return False

    for _, count in minute_buckets[-CONSECUTIVE_TIME:]:
        if count < ERROR_THRESHOLD:
            return False

    return True


def fetch_recent_error_logs(
    db: Session,
    service: str,
    window_start: datetime,
    window_end: datetime
) -> List[Dict[str, Any]]:
    """
    Fetch logs to pass into AI analysis
    """
    logs = (
        db.query(models.Log)
        .filter(
            models.Log.service == service,
            models.Log.level == "ERROR",
            models.Log.timestamp >= window_start,
            models.Log.timestamp <= window_end
        )
        .order_by(models.Log.timestamp.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "timestamp": log.timestamp.isoformat(),
            "service": log.service,
            "level": log.level,
            "message": log.message,
            "trace_id": getattr(log, 'trace_id', None)
        }
        for log in logs
    ]


def detect_and_create_incidents(db: Session):
    """
    Main detection pipeline with pattern matching
    """
    logger.info("Running incident detection...")

    # 1️⃣ SPIKE-BASED DETECTION (existing)
    spikes = check_error_rate(db)

    for spike in spikes:
        service = spike["service"]
        logger.info(
            f"Checking service {service} with {spike['error_count']} errors"
        )

        if not check_consecutive_spikes(db, service):
            logger.info(f"No sustained spike for {service}")
            continue

        logger.info(
            f"✅ {service} has sustained spike for {CONSECUTIVE_TIME} minutes"
        )

        # Prevent duplicate incidents
        existing = get_open_incident_for_service(db, service)
        if existing:
            logger.info(f"Incident already exists for {service}")
            continue

        # 🔥 FETCH LOGS FOR AI
        recent_logs = fetch_recent_error_logs(
            db,
            service,
            spike["window_start"],
            spike["window_end"]
        )

        # 🔥 PASS LOGS INTO INCIDENT SERVICE
        spike["logs"] = recent_logs

        # 🚨 CREATE THE INCIDENT
        incident = create_incident_from_spike(db, spike)
        logger.info(f"🚨 Created incident #{incident.id} for {service}")

        # 🔔 SEND NOTIFICATIONS THROUGH ALL CHANNELS
        try:
            from backend.services.notifier import notifier
            notifier.send_all(incident)
            logger.info(f"🔔 Notifications sent for incident #{incident.id}")
        except Exception as e:
            logger.error(f"❌ Failed to send notifications for incident #{incident.id}: {e}")

    # 2️⃣ PATTERN-BASED DETECTION (NEW)
    try:
        matcher = get_pattern_matcher(db)
        pattern_matches = matcher.match_recent_errors(minutes=TIME_WINDOW)
        
        if pattern_matches:
            logger.info(f"📊 Found {len(pattern_matches)} pattern matches")
            
            # Group by pattern for better logging
            pattern_summary = {}
            for match in pattern_matches:
                pattern = match["pattern"]
                if pattern not in pattern_summary:
                    pattern_summary[pattern] = {
                        "count": 0,
                        "services": set(),
                        "runbook": match["suggested_runbook"]
                    }
                pattern_summary[pattern]["count"] += 1
                pattern_summary[pattern]["services"].add(match["service"])
            
            # Log summary
            for pattern, data in pattern_summary.items():
                logger.info(
                    f"  - {pattern}: {data['count']} matches "
                    f"in {', '.join(data['services'])} "
                    f"(runbook: {data['runbook']})"
                )
            
            # 🔥 TODO: Create pattern-based incidents
            # You could create a different type of incident for pattern matches
            
    except Exception as e:
        logger.error(f"❌ Pattern matching failed: {e}")

    logger.info("Detection complete")


# ---------------- RUNNERS ---------------- #

def detector_loop(interval_seconds: int = 60):
    """
    Run detector continuously (background mode)
    """
    logger.info(f"Starting detector loop (interval: {interval_seconds}s)")

    while True:
        try:
            db = SessionLocal()
            detect_and_create_incidents(db)
            db.close()
        except Exception as e:
            logger.error(f"Detector error: {e}")

        time.sleep(interval_seconds)


if __name__ == "__main__":
    db = SessionLocal()
    detect_and_create_incidents(db)
    db.close()