import logging
from sqlalchemy.orm import Session
from backend import crud
from backend.services.solution_generator import generate_solution_for_incident
from backend.models import Runbook

logger = logging.getLogger(__name__)


class RecommendationService:

    def __init__(self, db: Session):
        self.db = db

    def get_recommendation(self, incident_id: int):
        """
        Generates recommendation and optionally saves it as a runbook.
        """

        # Check incident
        incident = crud.get_incident(self.db, incident_id)
        if not incident:
            return {"error": "Incident not found", "status": 404}

        try:
            # Generate AI solution
            solution = generate_solution_for_incident(self.db, incident_id)

            # Save solution as runbook
            self._save_solution_as_runbook(incident, solution)

            return solution

        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return {
                "error": "Failed to generate recommendation",
                "details": str(e),
                "status": 500
            }

    def _save_solution_as_runbook(self, incident, solution):
        """
        Converts AI solution into a reusable runbook
        """

        try:

            content = "\n".join(solution.get("immediate_actions", []))

            runbook = Runbook(
                service=incident.title.split("in ")[-1].split()[0]
                if "in " in incident.title else "unknown",
                error_type="ai_generated",
                title=f"AI Fix for Incident {incident.id}",
                content=content,
                tags=["ai_generated"]
            )

            self.db.add(runbook)
            self.db.commit()

            logger.info(f"Runbook auto-created for incident {incident.id}")

        except Exception as e:
            logger.warning(f"Runbook save skipped: {e}")