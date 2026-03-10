from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from backend.database import get_db
from backend import crud
from backend.services.runbook_service import RunbookService
from backend.services.solution_generator import generate_solution_for_incident

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["Agent Router"]
)

@router.post("/process-incident/{incident_id}")
def process_incident(
    incident_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:

    logger.info(f"Agent Processing incident {incident_id}")

    incident = crud.get_incident(db, incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    reasoning = crud.get_incident_reasoning(db, incident_id)

    runbook_service = RunbookService(db)

    matches = runbook_service.match_runbooks_for_incident(incident_id)

    if matches and len(matches) > 0:
        best_match = matches[0]
        runbook = best_match["runbook"]

        full_runbook = crud.get_runbook_by_service_type(
            db,
            runbook.service,
            runbook.error_type
        )

        # Safety check if runbook exists in DB
        if not full_runbook:
            full_runbook_content = "Runbook details missing in database."
            full_runbook_id = 0
            full_runbook_title = "Unknown Runbook"
        else:
            full_runbook_content = full_runbook.content
            full_runbook_id = full_runbook.id
            full_runbook_title = full_runbook.title

        commands = runbook_service._extract_commands_from_runbook(full_runbook) if full_runbook else []
        suggestion = runbook_service.get_suggested_fix(incident_id)

        response = {
            "incident_id": incident_id,
            "decision": "use_runbook",
            "confidence": best_match["confidence"],
            "score": best_match["score"],
            "runbook": {
                "id": full_runbook_id,
                "service": runbook.service,
                "error_type": runbook.error_type,
                "title": full_runbook_title,
                "content": (
                    full_runbook_content[:200] + "..."
                    if full_runbook_content and len(full_runbook_content) > 200
                    else full_runbook_content
                )
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
        solution = generate_solution_for_incident(db, incident_id)

        response = {
            "incident_id": incident_id,
            "decision": "ai_solution",
            "confidence": "MEDIUM",
            "reason": "No matching runbooks found",
            "ai_analysis": {
                "summary": reasoning.ai_summary if reasoning else None,
                "keywords": reasoning.keywords if reasoning else [],
                "root_cause": reasoning.root_cause if reasoning else None,
            },
            "ai_solution": solution,
            "next_steps": [
                "Review AI generated solution",
                "Apply commands if safe",
                "Create runbook if solution works"
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
    logger.info(f"Feedback received for incident {incident_id}: {feedback}")
    return {
        "status": "feedback recorded",
        "incident_id": incident_id,
        "feedback": feedback
    }


@router.get("/status/{incident_id}")
def agent_status(
    incident_id: int,
    db: Session = Depends(get_db)
):
    return {
        "incident_id": incident_id,
        "status": "processed",
        "agent_version": "1.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.post("/generate-solution/{incident_id}")
def generate_solution_endpoint(
    incident_id: int,
    db: Session = Depends(get_db)
):
    solution = generate_solution_for_incident(db, incident_id)
    return solution


@router.get("/incidents")
def list_incidents_for_agent(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    incidents = crud.get_incidents(db, skip=skip, limit=limit)
    return [
        {
            "id": i.id,
            "title": i.title,
            "severity": i.severity,
            "status": i.status,
            "service": getattr(i, "service", "unknown"),
            "error_count": i.error_count,
            "detected_at": i.detected_at.isoformat()
        }
        for i in incidents
    ]


@router.get("/processing-status/{incident_id}")
def get_incident_status(
    incident_id: int,
    db: Session = Depends(get_db)
):
    return {
        "incident_id": incident_id,
        "processed": False,
        "last_action": None,
        "timestamp": datetime.now().isoformat()
    }

# ---------------- AGENT RUNTIME CONTROL ---------------- #

agent_running = False


@router.post("/start")
def start_agent():
    global agent_running
    agent_running = True

    logger.info("Agent started")

    return {
        "status": "started",
        "running": True
    }


@router.post("/stop")
def stop_agent():
    global agent_running
    agent_running = False

    logger.info("Agent stopped")

    return {
        "status": "stopped",
        "running": False
    }


@router.get("/status")
def agent_runtime_status():
    return {
        "running": agent_running
    }