from google import genai
from google.genai import types 
import json
import logging
from typing import Dict, Any, List
from backend.config import GEMINI_API_KEY, LOG_LEVEL

logger = logging.getLogger(__name__)
logging.basicConfig(level=getattr(logging, LOG_LEVEL))

MODEL_NAME = "models/gemini-2.5-flash"

client = genai.Client(api_key=GEMINI_API_KEY)

def analyze_incident(
    logs: List[Dict[str, Any]],
    service: str | None = None
) -> str:
    """
    Analyze incident logs using Gemini.
    Returns JSON as STRING (DB-safe).
    """
    try:
        # 1. Format logs for the prompt
        log_text = "\n".join([
            f"[{log.get('timestamp')}] {log.get('service')} : {log.get('message')}"
            for log in logs[:20]
        ])

        prompt = f"""
        You are an SRE analyzing a production incident.
        Service: {service or 'Multiple'}
        Logs:
        {log_text}

        Analyze the root cause and provide a report.
        """

        # 2. Use JSON Mode (New SDK Feature)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "summary": {"type": "STRING"},
                        "root_cause_hypothesis": {"type": "STRING"},
                        "severity_score": {"type": "INTEGER"},
                        "severity_level": {"type": "STRING"},
                        "affected_services": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "key_errors": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "recommended_actions": {"type": "ARRAY", "items": {"type": "STRING"}},
                    },
                    "required": ["summary", "root_cause_hypothesis", "severity_score", "severity_level"]
                }
            )
        )

        # In JSON mode, response.text is guaranteed to be a JSON string
        return response.text 

    except Exception as e:
        logger.warning(f"Gemini analysis failed: {e}")
        # Return a standard JSON string so the database always gets valid JSON
        return json.dumps({
            "summary": "AI analysis unavailable",
            "root_cause_hypothesis": str(e),
            "severity_score": 50,
            "severity_level": "MEDIUM",
            "affected_services": [service] if service else [],
            "key_errors": [],
            "recommended_actions": ["Manual investigation required"]
        }, indent=2)

def extract_keywords(logs: List[Dict[str, Any]]) -> List[str]:
    """
    Extract technical keywords from logs.
    """
    try:
        log_text = "\n".join([log.get("message", "") for log in logs[:10]])
        prompt = f"Extract 5 technical keywords from these logs as a JSON array of strings: {log_text}"

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )

        # Parse and return as a Python list
        keywords = json.loads(response.text)
        return keywords if isinstance(keywords, list) else []

    except Exception as e:
        logger.warning(f"Keyword extraction failed: {e}")
        return []