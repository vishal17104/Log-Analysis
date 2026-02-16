from sqlalchemy.orm import Session
from backend import models, crud, schemas
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_incident_from_spike(
    db: Session,
    spike_data: dict
) -> models.Incident:
    """
    Create an incident from detector spike data
    """

    incident_data = schemas.IncidentCreate(
        title=f"Error spike in {spike_data['service']} service",
        severity=spike_data["severity"],
        error_count=spike_data["error_count"],
        window_start=spike_data["window_start"],
        window_end=spike_data["window_end"],
        status="open",
        created_at=datetime.utcnow()
    )

    incident = crud.create_incident(db, incident_data)

    logger.info(
        f"Incident created for {spike_data['service']} "
        f"(severity={spike_data['severity']})"
    )

    return incident


def get_open_incident_for_service(
    db: Session,
    service: str
):
    """
    Check if an open incident already exists for a service
    """
    return (
        db.query(models.Incident)
        .filter(
            models.Incident.title.contains(service),
            models.Incident.status == "open"
        )
        .first()
    )
