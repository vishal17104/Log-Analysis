from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class LogCreate(BaseModel):
    timestamp: datetime
    service: str = Field(..., max_length=50)
    level: Literal["INFO", "WARNING", "ERROR"]
    message: str = Field(..., max_length=500)


class LogResponse(LogCreate):
    id: int

    class Config:
        from_attributes = True
