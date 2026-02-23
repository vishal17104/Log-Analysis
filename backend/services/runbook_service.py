from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
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
            logger.warning(f"Incident #{incident_id} not found")
            return []
        
        reasoning = crud.get_incident_reasoning(self.db, incident_id)
        
        #Extract matching criteria
        service = incident.title.split('in')[-1].split(' ')[0] if 'in ' in incident.title else None

        #Get keywords from AI analysis or generate from logs
        keywords = reasoning.keywords if reasoning and reasoning.keywords else []

        #Add error type based on severity and keywords

        error_type = self._classify_error_type(incident.severity, keywords)

        logger.info(f"Matching runbooks for {service} with keywords: {keywords}, type: {error_type}")

        #find matching runbooks
        matched_runbooks = crud.match_runbooks_by_criteria(self.db, service = service, error_type = error_type, keywords = keywords)

        #score and rank
        scored_runbooks = []
        for runbook in matched_runbooks:
            score = self._calculate_relevance_score(
                runbook, servcie = service, error_type = error_type, keywords = keywords
            )
            scored_runbooks.append({
                 "runbook": {
                    "id": runbook.id,
                    "name": runbook.name,
                    "title": runbook.title,
                    "description": runbook.description if hasattr(runbook, 'description') else "",
                    "tags": runbook.tags
                },
                "score": score,
                "confidence": self._score_to_confidence(score)
            })

        #sort by score descending
        scored_runbooks.sort(key=lambda x: x["score"], reverse=True)

        return scored_runbooks

    def _classify_error_type(self, keywords: List[str], severity: str) -> str:
        """Classify error type based on keywords and severity"""
        error_type_map = {
            'timeout': ['timeout', 'timed out', 'deadline', 'slow'],
            'connection': ['connection', 'refused', 'disconnect', 'network'],
            'database': ['database', 'postgres', 'sql', 'query', 'db'],
            'memory': ['memory', 'heap', 'leak', 'oom'],
            'api': ['api', 'endpoint', 'http', 'rest'],
            'auth': ['auth', 'login', 'permission', 'unauthorized']
        }
        
        for err_type, patterns in error_type_map.items():
            if any(pattern in ' '.join(keywords).lower() for pattern in patterns):
                return err_type
        
        return 'unknown'
    
    def _calculate_relevance_score(
        self, 
        runbook: models.Runbook,
        service: Optional[str] = None,
        error_type: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> float:
        """Calculate relevance score (0-100)"""
        score = 0.0
        runbook_tags = runbook.tags or []
        
        # Service match (highest weight)
        if service and service.lower() in [t.lower() for t in runbook_tags]:
            score += 40
        
        # Error type match
        if error_type and error_type.lower() in [t.lower() for t in runbook_tags]:
            score += 30
        
        # Keyword matches
        if keywords:
            keyword_matches = 0
            for kw in keywords:
                if kw.lower() in ' '.join(runbook_tags).lower():
                    keyword_matches += 1
                elif kw.lower() in runbook.content.lower():
                    keyword_matches += 0.5
            score += min(keyword_matches * 10, 30)  # Max 30 points from keywords
        
        return min(score, 100)  # Cap at 100
    
    def _score_to_confidence(self, score: float) -> str:
        """Convert numerical score to confidence level"""
        if score >= 80:
            return "HIGH"
        elif score >= 50:
            return "MEDIUM"
        else:
            return "LOW"
        
    def get_suggested_fix(self, incident_id: int) -> Dict[str, Any]:
        """
        Get suggested fix for an incident based on best matching runbook
        """
        matches = self.match_runbooks_for_incident(incident_id)
        
        if not matches:
            return {
                "has_suggestion": False,
                "message": "No matching runbooks found",
                "confidence": "LOW"
            }
        
        best_match = matches[0]
        runbook = best_match["runbook"]
        
        # Extract specific commands from runbook (simplified)
        commands = self._extract_commands_from_runbook(
            crud.get_runbook_by_name(self.db, runbook["name"])
        )
        
        return {
            "has_suggestion": True,
            "runbook": runbook,
            "confidence": best_match["confidence"],
            "score": best_match["score"],
            "commands": commands,
            "message": f"Found matching runbook: {runbook['title']}"
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
        
        return commands[:3]  # Return top 3 commands

def suggest_fix_for_incident(db: Session, incident_id: int):
    service = RunbookService(db)
    return service.get_suggested_fix(incident_id)

def match_runbooks_for_incident(db: Session, incident_id: int):
    service = RunbookService(db)
    return service.match_runbooks_for_incident(incident_id)
