from datetime import datetime
import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from backend import models, crud

from google import genai

load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

MODEL_NAME = "gemini-2.5-flash"

# Initialize Gemini client once
client = genai.Client(api_key=API_KEY)


class SolutionGenerator:
    """Generates specific solutions for incidents using AI"""

    def __init__(self, db: Session):
        self.db = db

    def generate_solution(self, incident_id: int, prompt_template: str = None) -> Dict[str, Any]:

        # Get incident
        incident = crud.get_incident(self.db, incident_id)
        reasoning = crud.get_incident_reasoning(self.db, incident_id)

        if not incident:
            return {"error": f"Incident {incident_id} not found"}

        # Get logs
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
                .limit(20)
                .all()
            )

        # Format logs
        log_text = (
            "\n".join(
                [f"[{log.timestamp}] {log.service}: {log.message}" for log in logs]
            )
            if logs
            else "No logs available"
        )

        # Default prompt
        if not prompt_template:
            prompt_template = self._get_default_prompt()

        # Safer service extraction
        service = "unknown"
        if incident.title and "in " in incident.title:
            try:
                service = incident.title.split("in ")[-1].split()[0]
            except Exception:
                pass

        context = {
            "incident_title": incident.title,
            "severity": incident.severity,
            "error_count": incident.error_count,
            "service": service,
            "ai_summary": reasoning.ai_summary if reasoning else "No AI summary available",
            "root_cause": reasoning.root_cause if reasoning else "Unknown",
            "keywords": reasoning.keywords if reasoning and reasoning.keywords else [],
            "logs": log_text,
        }

        prompt = prompt_template.format(**context)

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            solution = self._parse_solution_response(response.text)

            solution["incident_id"] = incident_id
            solution["generated_at"] = str(datetime.utcnow())
            solution["model_used"] = MODEL_NAME

            return solution

        except Exception as e:
            logger.exception("Error generating solution")

            return {
                "incident_id": incident_id,
                "error": str(e),
                "fallback_solution": self._get_fallback_solution(context),
            }

    def _get_default_prompt(self) -> str:
        return """
You are an SRE (Site Reliability Engineer) tasked with creating a solution for a production incident.

INCIDENT DETAILS:
- Title: {incident_title}
- Severity: {severity}
- Affected Service: {service}
- Error Count: {error_count}

AI ANALYSIS:
- Summary: {ai_summary}
- Root Cause Hypothesis: {root_cause}
- Keywords: {keywords}

ERROR LOGS:
{logs}

TASK:
Based on the above information, provide a detailed solution for this incident.

YOUR SOLUTION MUST INCLUDE:
1. IMMEDIATE ACTIONS: Step-by-step commands to run right now
2. VERIFICATION: How to confirm the fix worked
3. ROOT CAUSE CONFIRMATION: What actually caused this
4. PREVENTION: How to prevent this in the future

FORMAT YOUR RESPONSE AS JSON:

{
    "immediate_actions": [
        "step 1 with actual command",
        "step 2 with actual command"
    ],
    "verification": "command or process to verify",
    "root_cause_confirmed": "brief explanation",
    "prevention": "steps to prevent recurrence",
    "estimated_resolution_time": "X minutes",
    "confidence": "HIGH|MEDIUM|LOW"
}

Be specific. Use actual Linux/bash commands where applicable.
"""

    def _parse_solution_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response to extract JSON solution"""

        try:

            # remove markdown
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            solution = json.loads(response_text)

            required = [
                "immediate_actions",
                "verification",
                "root_cause_confirmed",
            ]

            for field in required:
                if field not in solution:
                    solution[field] = f"Missing {field} from AI"

            return solution

        except json.JSONDecodeError as e:

            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response: {response_text}")

            return {
                "error": "Failed to parse AI response",
                "raw_response": response_text[:500],
                "immediate_actions": ["Manual investigation required"],
                "verification": "Check logs manually",
                "root_cause_confirmed": "AI parsing failed",
            }

    def _get_fallback_solution(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback solution when AI fails"""

        service = context.get("service", "unknown")

        return {
            "immediate_actions": [
                f"Check {service} service logs: kubectl logs -l service={service}",
                f"Restart {service} service: kubectl rollout restart deployment/{service}",
                "Check dependent services",
            ],
            "verification": f"curl -f http://{service}/health",
            "root_cause_confirmed": "AI analysis unavailable - manual investigation needed",
            "prevention": "Set up better monitoring and alerts",
            "estimated_resolution_time": "15 minutes",
            "confidence": "LOW",
            "note": "This is a fallback solution - AI generation failed",
        }


def generate_solution_for_incident(db: Session, incident_id: int, template: str = None):

    generator = SolutionGenerator(db)
    return generator.generate_solution(incident_id, template)