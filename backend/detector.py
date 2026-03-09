from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import time
import logging

from backend import models
from backend.database import SessionLocal
from backend.services.incident_service import create_incident_from_spike, get_open_incident_for_service
from backend.services.pattern_matcher import get_pattern_matcher

# ---------------- CONFIG ---------------- #
ERROR_THRESHOLD = 5              # Increased slightly for better testing
TIME_WINDOW = 5                  # Look back 5 minutes
CONSECUTIVE_TIME = 2             # Minutes sustained

SEVERITY_THRESHOLDS = {"CRITICAL": 50, "HIGH": 20, "MEDIUM": 10, "LOW": 5}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- DETECTION LOGIC ---------------- #

def check_error_rate(db: Session) -> List[Dict[str, Any]]:
    # Standardize on UTC
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=TIME_WINDOW)
    
    error_counts = (
        db.query(models.Log.service, func.count().label("error_count"))
        .filter(models.Log.level == "ERROR", models.Log.timestamp >= cutoff)
        .group_by(models.Log.service).all()
    )

    results = []
    for service, count in error_counts:
        if count >= ERROR_THRESHOLD:
            severity = "LOW"
            for level, threshold in SEVERITY_THRESHOLDS.items():
                if count >= threshold: severity = level

            results.append({
                "service": service,
                "error_count": count,
                "severity": severity,
                "window_start": cutoff,
                "window_end": datetime.now(timezone.utc)
            })
    return results

def check_consecutive_spikes(db: Session, service: str) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=CONSECUTIVE_TIME)
    minute_buckets = (
        db.query(func.date_trunc("minute", models.Log.timestamp).label("minute"), func.count().label("count"))
        .filter(models.Log.service == service, models.Log.level == "ERROR", models.Log.timestamp >= cutoff)
        .group_by("minute").order_by("minute").all()
    )
    if len(minute_buckets) < CONSECUTIVE_TIME: return False
    return all(count >= ERROR_THRESHOLD for _, count in minute_buckets[-CONSECUTIVE_TIME:])

def fetch_recent_error_logs(db: Session, service: str, window_start: datetime, window_end: datetime):
    logs = (
        db.query(models.Log)
        .filter(models.Log.service == service, models.Log.level == "ERROR", 
                models.Log.timestamp >= window_start, models.Log.timestamp <= window_end)
        .order_by(models.Log.timestamp.desc()).limit(20).all()
    )
    return [{"timestamp": l.timestamp.isoformat(), "service": l.service, "message": l.message} for l in logs]

def detect_and_create_incidents(db: Session):
    logger.info("Running incident detection...")
    
    # 1️⃣ SPIKE-BASED DETECTION
    spikes = check_error_rate(db)
    for spike in spikes:
        service = spike["service"]
        if not check_consecutive_spikes(db, service): continue

        if get_open_incident_for_service(db, service):
            logger.info(f"Incident already exists for {service}")
            continue

        # FETCH LOGS FOR AI & NOTIFIER
        spike["logs"] = fetch_recent_error_logs(db, service, spike["window_start"], spike["window_end"])
        
        incident = create_incident_from_spike(db, spike)
        logger.info(f"🚨 Created incident #{incident.id} for {service}")

    # 2️⃣ PATTERN-BASED DETECTION
    try:
        matcher = get_pattern_matcher(db)
        pattern_matches = matcher.match_recent_errors(minutes=TIME_WINDOW)
        if pattern_matches:
            logger.info(f"📊 Found {len(pattern_matches)} pattern matches")
            # Log summary logic remains here...
    except Exception as e:
        logger.error(f"❌ Pattern matching failed: {e}")

if __name__ == "__main__":
    while True:
        db_session = SessionLocal()
        try:
            detect_and_create_incidents(db_session)
        finally:
            db_session.close()
        time.sleep(60) # Run every minute