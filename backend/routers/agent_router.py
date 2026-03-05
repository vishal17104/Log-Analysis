from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from backend.database import get_db
from backend import crud
from backend.services.runbook_service import RunbookService
from backend.services.solution_generator import SolutionGenerator
from backend.prompts.solution_templates import get_template_for_incident
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["Agent Router"]
)

@router.post("/process-incident/{incident_id}")
def process_incident(incident_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Agent router that processes an incident and decides next action."""

    logger.info(f"Agent Processing incident {incident_id}")

    #Fetch incident
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    #Get AI reasoning
    reasoning = crud.get_incident_reasoning(db, incident_id)
    
    #Initialize runbook service
    runbook_service = RunbookService(db)

    #Match runbooks
    matches = runbook_service.match_runbooks_for_incident(incident_id)

    #Decision Logic
    if matches and len(matches) > 0:
        best_match = matches[0]
        runbook = best_match["runbook"]

        full_runbook = crud.get_runbook_by_service_type(db, runbook.service, runbook.error_type)

        
        commands = runbook_service._extract_commands_from_runbook(full_runbook)

        #Get suggested fix

        suggestion = runbook_service.get_suggested_fix(incident_id)

        response = {
            "incident_id": incident_id,
            "decision": "use_runbook",
            "confidence": best_match["confidence"],
            "score": best_match["score"],
            "runbook": {
                "id": full_runbook.id,
                "service": full_runbook.service,
                "error_type": full_runbook.error_type,
                "title": full_runbook.title,
                "content": full_runbook.content[:200] + "..." if len(full_runbook.content) else ""
            },
            "commands": commands,
            "suggested_fix": suggestion.get("message", "Use matching runbook"),
            "ai_analysis": {
                "summary": reasoning.ai_summary if reasoning else None,
                "keywords": reasoning.keywords if reasoning else [],
                "root_cause": reasoning.root_cause if reasoning else None,
            },
            "next_steps": [
                "Present runbook to user",
                "Await human feedback",
                "Execute suggested commands"
            ]       
        }
    
    else:
        response = {
            "incident_id": incident_id,
            "decision": "escalate_to_human",
            "confidence": "LOW",
            "reason": "No matching runbooks found",
            "ai_analysis": {
                "summary": reasoning.ai_summary if reasoning else "No AI analysis available",
                "keywords": reasoning.keywords if reasoning else [],
                "root_cause": reasoning.root_cause if reasoning else "Unknown",
            },
            "suggested_actions": [
                "Manual investigation required",
                "Create new runbook for this error pattern",
                "Check logs manually"
            ],
            "next_steps": [
                "Escalate to on-call engineer",
                "Log as new incident type",
                "Consider creating runbook"
            ]
        }

    logger.info(f"Agent decision for incident {incident_id}: {response['decision']}")

    return response

@router.post("/feedback/{incident_id}")
def agent_feedback(
    incident_id: int,
    feedback: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Human feedback on agent decision"""

    logger.info(f"Feedback received for incident {incident_id}: {feedback}")

    # Store feedback in database (you'll need a feedback table)
    # This can be used to fine-tune the agent

    return{
        "status": "feedback recorded",
        "incident_id": incident_id,
        "feedback": feedback
    }

@router.get("/status/{incident_id}")
def agent_status(
    incident_id: int,
    db: Session = Depends(get_db)
):
    "Get current agent status from an incident"
    # This could track the state of the incident through the agent pipeline
    return {
        "incident_id": incident_id,
        "status": "processed",
        "agent_version": "1.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@router.post("/generate-solution/{incident_id}")
def generate_solution(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """Generate AI solution for an incident"""
    generator = SolutionGenerator(db)
    
    #Get incident to determine template
    incident = crud.get_incident(db, incident_id)
    reasoning = crud.get_incident_reasoning(db, incident_id)
    
    #Select appropriate template
    service = incident.title.split('in ')[-1].split(' ')[0] if 'in ' in incident.title else "unknown"
    keywords = reasoning.keywords if reasoning and reasoning.keywords else []
    template = get_template_for_incident(service, keywords)
    
    solution = generator.generate_solution(incident_id, template)
    return solution
