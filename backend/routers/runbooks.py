from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import crud
from ..schemas import RunbookCreate, RunbookUpdate, RunbookResponse
from ..services.runbook_service import RunbookService

router = APIRouter(
    prefix="/runbooks",
    tags=["Runbooks"]
)

@router.post("", response_model=RunbookResponse, status_code=status.HTTP_201_CREATED)
def create_runbook(payload: RunbookCreate, db: Session = Depends(get_db)):
    """Create a new runbook"""
    service = RunbookService(db)

    name = f"{payload.service}_{payload.error_type}.md"

    runbook = service.create_runbook(
        name=name,
        service=payload.service,
        error_type=payload.error_type,
        title=payload.title,
        content=payload.content,
        tags=payload.tags or [payload.service, payload.error_type]
    )

    return runbook


@router.get("/", response_model=list[RunbookResponse])
def list_runbooks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all runbooks"""
    return crud.get_all_runbooks(db, skip=skip, limit=limit)


@router.post("/match-for-incident/{incident_id}")
def match_for_incident(incident_id: int, db: Session = Depends(get_db)):
    """Find matching runbooks for an incident"""
    service = RunbookService(db)
    matches = service.match_runbooks_for_incident(incident_id)
    return {"incident_id": incident_id, "matches": matches}


@router.get("/suggest-fix/{incident_id}")
def suggest_fix(incident_id: int, db: Session = Depends(get_db)):
    """Get suggested fix for an incident"""
    service = RunbookService(db)
    return service.get_suggested_fix(incident_id)


@router.get("/{service}/{error_type}", response_model=RunbookResponse)
def get_runbook(service: str, error_type: str, db: Session = Depends(get_db)):
    """Get runbook by service and error type"""
    runbook = crud.get_runbook_by_service_type(db, service, error_type)

    if not runbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Runbook for {service}/{error_type} not found"
        )

    return runbook


@router.put("/{service}/{error_type}", response_model=RunbookResponse)
def update_runbook(service: str, error_type: str, payload: RunbookUpdate, db: Session = Depends(get_db)):
    """Update runbook"""
    runbook = crud.get_runbook_by_service_type(db, service, error_type)

    if not runbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Runbook for {service}/{error_type} not found"
        )

    if payload.title is not None:
        runbook.title = payload.title
    if payload.content is not None:
        runbook.content = payload.content
    if payload.tags is not None:
        runbook.tags = payload.tags

    db.commit()
    db.refresh(runbook)
    return runbook


@router.delete("/{service}/{error_type}", status_code=status.HTTP_204_NO_CONTENT)
def delete_runbook(service: str, error_type: str, db: Session = Depends(get_db)):
    """Delete runbook"""
    runbook = crud.get_runbook_by_service_type(db, service, error_type)

    if not runbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Runbook for {service}/{error_type} not found"
        )

    db.delete(runbook)
    db.commit()