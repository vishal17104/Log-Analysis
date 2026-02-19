from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time
import logging
from backend import models, crud, schemas
from backend.database import SessionLocal


ERROR_THRESHOLD = 2
TIME_WINDOW = 10
CONSECUTIVE_TIME = 2
SEVERITY_THRESHOLDS = {
    "CRITICAL": 50,
    "HIGH": 20,
    "MEDIUM": 10,
    "LOW": 5
}


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_error_rate(db: Session) -> List[Dict[str, Any]]:
    """Check error rates per service for last minute"""

    cutoff = datetime.utcnow() - timedelta(minutes=TIME_WINDOW)

    error_count = db.query(models.Log.service, func.count().label('error_count')).filter(models.Log.level == 'ERROR', models.Log.timestamp >= cutoff).group_by(models.Log.service).all()

    result = []

    for service, count in error_count:
        if count >= ERROR_THRESHOLD:
            severity = "LOW"
            for level, threshold in SEVERITY_THRESHOLDS.items():
                if count >= threshold:
                    severity = level

            result.append({
                "service": service,
                "error_count": count,
                "severity": severity,
                "window_start": cutoff,
                "window_end": datetime.utcnow()
            })
            logger.info(f"High errors in {service}: {count} errors/min ({severity})")

    return result

def create_incident(db: Session, spike_data: Dict[str, Any]) -> models.Incident:
    """Create an incident based on spike data"""
    try:
        incident = schemas.IncidentCreate(
            title=f"Error spike in {spike_data['service']} service",
            severity=spike_data['severity'],
            error_count=spike_data['error_count'],
            window_start=spike_data['window_start'],
            window_end=spike_data['window_end']
        )

        db_incident = crud.create_incident(db, incident)
        logger.info(f"✅ Incident created successfully with ID: {db_incident.id}")
        return db_incident
    except Exception as e:
        logger.error(f"❌ Failed to create incident: {e}")
        raise e

def check_consecutive_spikes(db: Session, service:str) -> bool:
    """Check if service has had high errors for consecutive minutes"""

    cutoff = datetime.utcnow() - timedelta(minutes=CONSECUTIVE_TIME)

    minutes_count = db.query(func.date_trunc('minute', models.Log.timestamp).label('minute'), func.count().label('count')).filter(models.Log.service == service, models.Log.level == 'ERROR', models.Log.timestamp >= cutoff).group_by('minute').all()

    # Check if we have data for all recent minutes
    expected_minutes = CONSECUTIVE_TIME
    if len(minutes_count) < expected_minutes:
        return False

    # Check if all minutes exceeded threshold
    for minute, count in minutes_count[-expected_minutes:]:
        if count < ERROR_THRESHOLD:
            return False
    
    return True

def detect_and_create_incidents(db: Session):
    """Detect and create incidents"""
    logger.info("Running incident detection...")

    #check current error rates
    spikes = check_error_rate(db)

    for spike in spikes:
        service = spike['service']
        logger.info(f"Checking service {service} with {spike['error_count']} errors")

        #check if this is a sustained issue
        if check_consecutive_spikes(db, service):
            logger.info(f"✅ {service} has sustained spike for {CONSECUTIVE_TIME} minutes")
            
            # Check if incident already exists for this service
            existing_incident = db.query(models.Incident).filter(
                models.Incident.title.contains(service), 
                models.Incident.status == 'open'
            ).first()

            if not existing_incident:
                # Create incident for this sustained spike
                incident = create_incident(db, spike)
                logger.info(f"🚨 Created incident #{incident.id} for {service}")
                # TODO: Trigger AI Analysis
            else:
                logger.info(f"Incident already exists for {service}")
        else:
            logger.info(f"No sustained spike for {service}")

    logger.info("Detection complete")

def detector_loop(interval_seconds = 60):
    """Run detector continuously (for background process)"""
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