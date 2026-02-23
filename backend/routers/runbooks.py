from fastapi import APIRouter, HTTPException, status
from ..schemas import (
    RunbookCreate,
    RunbookUpdate,
    RunbookResponse
)
from ..services.runbook_service import RunbookService

router = APIRouter(
    prefix="/runbooks",
    tags=["Runbooks"]
)


@router.post(
    "",
    response_model=RunbookResponse,
    status_code=status.HTTP_201_CREATED
)
def create_runbook(payload: RunbookCreate):
    """
    Create a new runbook.
    Stored as: runbooks/{service}/{error_type}/solution.md
    """
    try:
        runbook_id = RunbookService.create_runbook(
            service=payload.service,
            error_type=payload.error_type,
            title=payload.title,
            solution=payload.solution
        )

        return RunbookResponse(
            id=runbook_id,
            service=payload.service,
            error_type=payload.error_type,
            title=payload.title,
            solution=payload.solution
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{service}/{error_type}",
    response_model=RunbookResponse
)
def get_runbook(service: str, error_type: str):
    """
    Fetch a runbook by service and error type.
    """
    try:
        title, solution = RunbookService.read_runbook(
            service=service,
            error_type=error_type
        )

        return RunbookResponse(
            id=f"{service}:{error_type}",
            service=service,
            error_type=error_type,
            title=title,
            solution=solution
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Runbook not found"
        )


@router.put(
    "/{service}/{error_type}",
    response_model=RunbookResponse
)
def update_runbook(
    service: str,
    error_type: str,
    payload: RunbookUpdate
):
    """
    Update an existing runbook.
    """
    try:
        RunbookService.update_runbook(
            service=service,
            error_type=error_type,
            title=payload.title,
            solution=payload.solution
        )

        title, solution = RunbookService.read_runbook(
            service=service,
            error_type=error_type
        )

        return RunbookResponse(
            id=f"{service}:{error_type}",
            service=service,
            error_type=error_type,
            title=title,
            solution=solution
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Runbook not found"
        )