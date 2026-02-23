from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, timezone
from typing import Literal, Optional, List, Dict, Any

# ---------------- LOG SCHEMAS ---------------- #

class LogCreate(BaseModel):
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    service: str = Field(..., max_length=50)
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    message: str = Field(..., min_length=1, max_length=500)

    host: Optional[str] = None
    pid: Optional[int] = None
    ip_address: Optional[str] = None
    status_code: Optional[int] = None
    trace_id: Optional[str] = None

    @field_validator("service")
    @classmethod
    def validate_service(cls, v):
        allowed_services = [
            "payment", "auth", "api", "worker", "frontend", "database"
        ]
        if v.lower() not in allowed_services:
            raise ValueError(f"Service must be one of {allowed_services}")
        return v.lower()

class LogResponse(LogCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class LogStats(BaseModel):
    total_logs: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    by_service: Dict[str, int]
    time_range: Dict[str, datetime]
    timeline: List[Dict[str, Any]]

# ---------------- INCIDENT SCHEMAS ---------------- #

class IncidentBase(BaseModel):
    title: str
    severity: str
    error_count: int
    window_start: datetime
    window_end: datetime

class IncidentCreate(IncidentBase):
    status: str = "open"

class IncidentResponse(IncidentBase):
    id: int
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    # ✅ NEW (Day 8)
    ai_analysis: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class IncidentStatusUpdate(BaseModel):
    status: str  # open, investigating, resolved

class IncidentDetailResponse(IncidentResponse):
    logs: List[dict] = []

class IncidentSummary(BaseModel):
    total_incidents: int
    open_incidents: int
    resolved_incidents: int
    by_severity: Dict[str, int]
    avg_resolution_time: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class RunbookBase(BaseModel):
    name: str
    title: Optional[str] = None
    content: str
    tags: Optional[List[str]] = []

class RunbookCreate(RunbookBase):
    pass

class RunbookUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class RunbookResponse(RunbookBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True