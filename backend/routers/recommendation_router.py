from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.recommendation_service import RecommendationService

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/{incident_id}")
def get_incident_recommendation(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """
    Get AI-generated solution recommendation for an incident.
    """

    service = RecommendationService(db)

    result = service.get_recommendation(incident_id)

    # Handle errors returned by service
    if isinstance(result, dict) and "error" in result:
        status_code = result.get("status", 400)
        raise HTTPException(
            status_code=status_code,
            detail=result["error"]
        )

    return result