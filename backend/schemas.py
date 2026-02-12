from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any


class LogCreate(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = Field(..., max_length=50)
    level: Literal["INFO", "WARNING", "ERROR"]
    message: str = Field(..., max_length=500)

    host: Optional[str] = Field(None, description="Hostname")
    pid: Optional[int] = Field(None, description="Process ID")
    ip_address: Optional[str] = Field(None, description="Client IP")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    trace_id: Optional[str] = Field(None, description="Distributed tracing ID")

    @validator('level')
    def validate_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if v not in allowed_levels:
            raise ValueError(f'Level must be one of {allowed_levels}')
        return v.upper()
    
    @validator('service')
    def validate_service(cls, v):
        allowed_services = ['payment', 'auth', 'api', 'worker', 'frontend', 'database']
        if v.lower() not in allowed_services:
            raise ValueError(f'Service must be one of {allowed_services}')
        return v.lower()

class LogResponse(LogCreate):
    id: int

    class Config:
        from_attributes = True


class LogStats(BaseModel):
    total_logs: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count:int
    by_service: Dict[str, int]
    time_range: Dict[str, datetime]
    timeline: List[Dict[str, Any]]

