from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend import models, crud
import logging

logger = logging.getLogger(__name__)


class RunbookService:
    """Service layer for runbook operations and matching logic"""

    def __init__(self, db: Session):
        self.db = db


    def match_runbooks_for_incident(self, incident_id: int) -> List[Dict[str, Any]]:
        """Find best matching runbooks for an incident"""

        incident = crud.get_incident(self.db, incident_id)
        if not incident:
            logger.warning(f"Incident {incident_id} not found")
            return []

        reasoning = crud.get_incident_reasoning(self.db, incident_id)

        # Extract service name from title
        service = incident.title.split('in ')[-1].split(' ')[0] if 'in ' in incident.title else None

        # Get keywords
        keywords = reasoning.keywords if reasoning and reasoning.keywords else []

        if not keywords:
            keywords = [service] if service else []
            if incident.severity:
                keywords.append(incident.severity.lower())

        error_type = self._classify_error_type(keywords, incident.severity)

        logger.info(
            f"Matching runbooks for {service} with error_type: {error_type}, keywords: {keywords}"
        )

        runbook = crud.get_runbook_by_service_type(self.db, service, error_type)

        if runbook:
            score = self._calculate_relevance_score(
                runbook, service=service, error_type=error_type, keywords=keywords
            )

            return [{
                "runbook": runbook,  
                "score": score,
                "confidence": self._score_to_confidence(score)
            }]

        return self._fallback_keyword_match(service, error_type, keywords)

    def get_suggested_fix(self, incident_id: int) -> Dict[str, Any]:
        """Get suggested fix for an incident"""

        matches = self.match_runbooks_for_incident(incident_id)

        if not matches:
            return {
                "has_suggestion": False,
                "message": "No matching runbooks found",
                "confidence": "LOW"
            }

        best_match = matches[0]
        runbook: models.Runbook = best_match["runbook"]

        commands = self._extract_commands_from_runbook(runbook)

        return {
            "has_suggestion": True,
            "runbook": {
                "id": runbook.id,
                "title": runbook.title,
                "service": runbook.service,
                "error_type": runbook.error_type,
                "content": runbook.content,
                "tags": runbook.tags
            },
            "confidence": best_match["confidence"],
            "score": best_match["score"],
            "commands": commands,
            "message": f"Found matching runbook: {runbook.title}"
        }

    def _extract_commands_from_runbook(self, runbook: models.Runbook) -> List[str]:
        """Extract shell commands from runbook markdown"""

        if not runbook or not runbook.content:
            return []

        commands = []
        lines = runbook.content.split('\n')
        in_code_block = False

        for line in lines:
            if line.startswith('```bash') or line.startswith('```'):
                in_code_block = not in_code_block
                continue

            if in_code_block and line.strip() and not line.startswith('#'):
                commands.append(line.strip())

        return commands[:3]

    def _classify_error_type(self, keywords: List[str], severity: str) -> str:
        error_type_map = {
            'timeout': ['timeout', 'timed out', 'deadline', 'slow'],
            'connection': ['connection', 'refused', 'disconnect', 'network'],
            'database': ['database', 'postgres', 'sql', 'query', 'db'],
            'memory': ['memory', 'heap', 'leak', 'oom'],
            'api': ['api', 'endpoint', 'http', 'rest'],
            'auth': ['auth', 'login', 'permission', 'unauthorized']
        }

        keyword_text = ' '.join(keywords).lower()

        for err_type, patterns in error_type_map.items():
            if any(pattern in keyword_text for pattern in patterns):
                return err_type

        return 'unknown'

    def _calculate_relevance_score(
        self,
        runbook: models.Runbook,
        service: Optional[str] = None,
        error_type: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> float:

        score = 0.0
        tags = runbook.tags or []

        if service and service.lower() in [t.lower() for t in tags]:
            score += 40

        if error_type and error_type.lower() in [t.lower() for t in tags]:
            score += 30

        if keywords:
            matches = 0
            for kw in keywords:
                if kw.lower() in ' '.join(tags).lower():
                    matches += 1
                elif runbook.content and kw.lower() in runbook.content.lower():
                    matches += 0.5

            score += min(matches * 10, 30)

        return min(score, 100)

    def _score_to_confidence(self, score: float) -> str:
        if score >= 80:
            return "HIGH"
        elif score >= 50:
            return "MEDIUM"
        return "LOW"


    def _fallback_keyword_match(self, service, error_type, keywords):

        all_runbooks = crud.get_all_runbooks(self.db)
        matches = []

        for runbook in all_runbooks:
            score = self._calculate_relevance_score(
                runbook, service=service, error_type=error_type, keywords=keywords
            )

            if score > 0:
                matches.append({
                    "runbook": runbook,
                    "score": score,
                    "confidence": self._score_to_confidence(score)
                })

        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:5]

    def create_runbook(self, service, error_type, content, title=None, tags=None, name=None):
        return crud.create_runbook_by_service(
            db=self.db,
            service=service,
            error_type=error_type,
            name=name,
            title=title,
            content=content,
            tags=tags
        )