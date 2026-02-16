from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time
import logging

from backend import models
from backend.database import SessionLocal
from backend.services.incident_service import (
    create_incident_from_spike,
    get_open_incident_for_service
)

# ---------------- CONFIG ---------------- #

ERROR_THRESHOLD = 10
TIME_WINDOW = 1          # minutes
CONSECUTIVE_TIME = 2     # minutes

SEVERITY_THRESHOLDS = {
    "CRITICAL": 50,
    "HIGH": 20,
    "MEDIUM": 10,
    "LOW": 5
}

# ---------------- LOGGING ---------------- #

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- DETECTOR LOGIC ---------------- #

def check_error_rate(db: Session) -> List[Dict[str, Any]]:
    """
    Check error rates per service for last TIME_WINDOW minutes
    """
    cutoff = datetime.utcnow() - timedelta(minutes=TIME_WINDOW)

    error_count = (
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

    for service, count in error_count:
        if count >= ERROR_THRESHOLD:
            severity = "LOW"
            for level, threshold in SEVERITY_THRESHOLDS.items():
                if count >= threshold:
                    severity = level

            spike = {
                "service": service,
                "error_count": count,
                "severity": severity,
                "window_start": cutoff,
                "window_end": datetime.utcnow()
            }

            results.append(spike)

            logger.info(
                f"High error rate detected | service={service} "
                f"errors={count}/min severity={severity}"
            )

    return results


def check_consecutive_spikes(db: Session, service: str) -> bool:
    """
    Check if a service has exceeded ERROR_THRESHOLD
    for CONSECUTIVE_TIME consecutive minutes
    """
    cutoff = datetime.utcnow() - timedelta(minutes=CONSECUTIVE_TIME)

    minutes_data = (
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

    if len(minutes_data) < CONSECUTIVE_TIME:
        return False

    for _, count in minutes_data[-CONSECUTIVE_TIME:]:
        if count < ERROR_THRESHOLD:
            return False

    return True


def detect_and_create_incidents(db: Session):
    """
    Main detection flow:
    Log → Detect → Check sustained spike → Create incident
    """
    logger.info("Running incident detection cycle...")

    spikes = check_error_rate(db)

    for spike in spikes:
        service = spike["service"]

        # Check sustained issue
        if not check_consecutive_spikes(db, service):
            continue

        # Check for existing open incident
        existing_incident = get_open_incident_for_service(db, service)

        if existing_incident:
            logger.info(f"Open incident already exists for service={service}")
            continue

        # Create new incident
        create_incident_from_spike(db, spike)

        # TODO (Day 7+): Trigger AI analysis here

    logger.info("Incident detection cycle completed")


# ---------------- BACKGROUND LOOP ---------------- #

def detector_loop(interval_seconds: int = 60):
    """
    Continuous detector loop (background process)
    """
    logger.info(f"Starting detector loop (interval={interval_seconds}s)")

    while True:
        try:
            db = SessionLocal()
            detect_and_create_incidents(db)
            db.close()
        except Exception as e:
            logger.error(f"Detector error: {e}")
        time.sleep(interval_seconds)


# ---------------- MANUAL RUN ---------------- #

if __name__ == "__main__":
    db = SessionLocal()
    detect_and_create_incidents(db)
    db.close()
