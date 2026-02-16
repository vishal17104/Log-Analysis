from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, timezone
from typing import Literal, Optional, List, Dict, Any

# ---------------- LOG SCHEMAS ---------------- #

class LogCreate(BaseModel):
    # Default factory ensures a timestamp is generated if not provided
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    service: str = Field(..., max_length=50)
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    # min_length=1 ensures the 'empty_string' chaos test fails correctly
    message: str = Field(..., min_length=1, max_length=500)

    # Optional metadata fields (required for your mock_data generator)
    host: Optional[str] = Field(None, description="Hostname")
    pid: Optional[int] = Field(None, description="Process ID")
    ip_address: Optional[str] = Field(None, description="Client IP")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    trace_id: Optional[str] = Field(None, description="Distributed tracing ID")

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
    # Use Pydantic v2 ConfigDict for SQLAlchemy compatibility
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

    model_config = ConfigDict(from_attributes=True)