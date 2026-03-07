import logging
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models
from pathlib import Path
from backend import crud

logger = logging.getLogger(__name__)

class PatternMatcher:
    """Keyword-based pattern matching"""

    def __init__(self, db: Session, config_path: str = "backend/config/patterns.yaml"):
        self.db = db
        self.patterns = self._load_patterns(config_path)
        logger.info(f"Loaded {len(self.patterns)} detection patterns from {config_path}")

    def _load_patterns(self, config_path: str) -> List[Dict[str, Any]]:
        """Load patterns from YAML file"""
        try:
            path = Path(config_path)
            if not path.exists():
                logger.error(f"Pattern file not found: {config_path}")
                return {}
            
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('patterns', {})
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            return {}
        
    def match_logs(self, logs: List[models.Log]) -> List[Dict[str, Any]]:
        """Match logs against patterns"""
        matches = []

        for log in logs:
            if log.level != "ERROR":
                continue
                
            for pattern_name, pattern in self.patterns.items():
                score = self._calculate_match_score(log, pattern)

                if score > 0:
                    matches.append({
                        "pattern": pattern_name,
                        "log_id": log.id,
                        "service": log.service,
                        "message": log.message[:100],
                        "score": score,
                        "severity_boost": pattern.get("severity_boost", 1.0),
                        "suggested_runbook": pattern.get("suggested_runbook"),
                        "timestamp": log.timestamp.isoformat() if log.timestamp else None
                    })

        return matches

    def match_recent_errors(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """Match recent errors against patterns"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        recent_errors = self.db.query(models.Log).filter(
            models.Log.level == 'ERROR',
            models.Log.timestamp >= cutoff
        ).all()
        
        return self.match_logs(recent_errors)
    
    def _calculate_match_score(self, log: models.Log, pattern: Dict) -> float:
        """Calculate how well a log matche a pattern(0 to 1)"""

        score = 0.0
        message_lower = log.message.lower()

        # Check keyword matches (60% weight)
        keywords = pattern.get("keywords", [])
        if keywords:
            keyword_matches = 0
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    keyword_matches += 1
            
            if keyword_matches > 0:
                score += 0.6 * (keyword_matches / len(keywords))

        # Check service match (40% weight)
        services = pattern.get("services", [])
        if services:
            service_lower = log.service.lower()
            for service in services:
                if service.lower() in service_lower:
                    score += 0.4
                    break
        
        return min(score, 1.0) 
    
    def get_incident_recommendations(self, incident_id: int) -> List[Dict[str, Any]]:
        """Get pattern based recommendation for an incident"""


        #Get logs for this incident
        incident = crud.get_incident(self.db, incident_id)

        if not incident or not incident.window_start or not incident.window_end:
            return []
        
        error_logs = self.db.query(models.Log).filter(
            models.Log.timestamp >= incident.window_start,
            models.Log.timestamp <= incident.window_end,
            models.Log.level == "ERROR"
        ).all()

        #Match logs against patterns
        matches = self.match_logs(error_logs)

        #Group by pattern and aggregate
        pattern_groups = {}

        for match in matches:
            pattern = match["pattern"]
            if pattern not in pattern_groups:
                pattern_groups[pattern] = {
                    "pattern": pattern,
                    "count": 0,
                    "total_score": 0,
                    "logs": [],
                    "suggested_runbook": match["suggested_runbook"],
                    "severity_boost": match["severity_boost"]
                }

            pattern_groups[pattern]["count"] += 1
            pattern_groups[pattern]["total_score"] += match["score"]
            pattern_groups[pattern]["logs"].append({
                "id": match["log_id"],
                "message": match["message"]
            })

            #Calculate avg score and sort

            recommendations = []
            for pattern, data in pattern_groups.items():
                avg_score = data["total_score"] / data["count"] if data["count"] > 0 else 0
                recommendations.append({
                    "pattern": pattern,
                    "confidence": self._score_to_confidence(avg_score),
                    "match_count": data["count"],
                    "avg_score": avg_score,
                    "suggested_runbook": data["suggested_runbook"],
                    "severity_boost": data["severity_boost"],
                    "sample_logs": data["logs"][:3] 
                })
            
            recommendations.sort(key=lambda x: (x["match_count"], x["avg_score"]), reverse=True)
        
        return recommendations
    
    def _score_to_confidence(self, score: float) -> str:
        """Convert score to confidence level"""
        if score >= 0.8:
            return "HIGH"
        elif score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
        
    def reload_patterns(self, config_path: str = "backend/config/patterns.yaml"):
        """Reload patterns from YAML"""
        self.patterns = self._load_patterns(config_path)
        logger.info(f"🔄 Reloaded {len(self.patterns)} patterns")
        return len(self.patterns)
    

_pattern_matcher = None

def get_pattern_matcher(db: Session):
    global _pattern_matcher
    if _pattern_matcher is None:
        _pattern_matcher = PatternMatcher(db)
    return _pattern_matcher
                    

