from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
from typing import Optional

from backend import models, crud, schemas
from backend.services.gemini_service import analyze_incident

logger = logging.getLogger(__name__)


def create_incident_from_spike(
    db: Session,
    spike_data: dict
) -> models.Incident:
    """
    Create an incident from detector spike data
    and enrich it with AI analysis (non-blocking).
    """

    # 1️⃣ Build incident payload
    incident_data = schemas.IncidentCreate(
        title=f"Error spike in {spike_data['service']} service",
        severity=spike_data["severity"],
        error_count=spike_data["error_count"],
        window_start=spike_data["window_start"],
        window_end=spike_data["window_end"],
        status="open"
    )
    incident = crud.create_incident(db, incident_data)

    logger.info(
        f"Incident created for {spike_data['service']} "
        f"(severity={spike_data['severity']})"
    )
    try:
        ai_result = analyze_incident(
            logs=spike_data.get("logs", []),
            service=spike_data["service"]
        )

        incident.ai_analysis = ai_result
        db.commit()
        db.refresh(incident)

        logger.info(
            f"AI analysis attached to incident #{incident.id}"
        )

    except Exception as e:
        logger.warning(
            f"AI analysis failed for incident #{incident.id}: {str(e)}"
        )

    return incident


def get_open_incident_for_service(
    db: Session,
    service: str
) -> Optional[models.Incident]:
    """
    Check if an open incident already exists for a service.
    Prevents duplicate incident creation.
    """
    return (
        db.query(models.Incident)
        .filter(
            models.Incident.title.contains(service),
            models.Incident.status == "open"
        )
        .first()
    )