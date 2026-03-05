import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from backend import models, crud

from google import genai
from google.genai import types

load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

MODEL_NAME = "gemini-1.5-flash"

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)


class SolutionGenerator:
    """Generates AI-powered incident solutions"""

    def __init__(self, db: Session):
        self.db = db

    def generate_solution(self, incident_id: int) -> Dict[str, Any]:

        # 1️⃣ Fetch incident
        incident = crud.get_incident(self.db, incident_id)
        if not incident:
            return {"error": f"Incident {incident_id} not found"}

        reasoning = crud.get_incident_reasoning(self.db, incident_id)

        # 2️⃣ Fetch related logs
        logs = []
        if incident.window_start and incident.window_end:
            logs = (
                self.db.query(models.Log)
                .filter(
                    models.Log.timestamp >= incident.window_start,
                    models.Log.timestamp <= incident.window_end,
                    models.Log.level == "ERROR",
                )
                .order_by(models.Log.timestamp)
                .limit(15)
                .all()
            )

        log_text = (
            "\n".join(
                [f"[{log.timestamp}] {log.service}: {log.message}" for log in logs]
            )
            if logs
            else "No logs available"
        )

        # 3️⃣ Build default prompt
        prompt = f"""
You are a Site Reliability Engineer (SRE) responding to a production incident.

INCIDENT DETAILS
Title: {incident.title}
Severity: {incident.severity}

AI ANALYSIS
Summary: {reasoning.ai_summary if reasoning else "N/A"}
Root Cause: {reasoning.root_cause if reasoning else "Unknown"}

RECENT ERROR LOGS
{log_text}

TASK:
Provide a JSON response with the following fields:

- immediate_actions (list of commands to run immediately)
- verification (how to confirm the fix worked)
- root_cause_confirmed (short explanation)
- prevention (steps to prevent recurrence)
- confidence (HIGH | MEDIUM | LOW)
"""

        try:

            # 4️⃣ Call Gemini with JSON Mode
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            # 5️⃣ Parse JSON safely
            solution = json.loads(response.text.strip())

            # Ensure required fields exist
            required_fields = [
                "immediate_actions",
                "verification",
                "root_cause_confirmed",
            ]

            for field in required_fields:
                if field not in solution:
                    solution[field] = f"Missing {field}"

            # Add metadata
            solution["incident_id"] = incident_id
            solution["generated_at"] = datetime.now(timezone.utc).isoformat()
            solution["model_used"] = MODEL_NAME

            return solution

        except Exception as e:
            logger.exception("AI Solution Generation Failed")

            # Extract service safely
            service = "unknown"

            if incident.title and "in " in incident.title:
                try:
                    service = incident.title.split("in ")[-1].split()[0]
                except Exception:
                    pass

            return self._get_fallback_solution(incident_id, service)

    def _get_fallback_solution(self, incident_id: int, service: str) -> Dict[str, Any]:
        """Fallback if AI generation fails"""

        return {
            "incident_id": incident_id,
            "immediate_actions": [
                f"kubectl logs -l service={service}",
                f"kubectl rollout restart deployment/{service}",
            ],
            "verification": "Check service health endpoint",
            "root_cause_confirmed": "Manual investigation required (AI fallback)",
            "prevention": "Review logs and add better monitoring",
            "confidence": "LOW",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "note": "Fallback solution used because AI generation failed",
        }


# Convenience wrapper
def generate_solution_for_incident(db: Session, incident_id: int):
    generator = SolutionGenerator(db)
    return generator.generate_solution(incident_id)