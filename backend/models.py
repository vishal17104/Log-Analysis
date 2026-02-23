from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# ---------------- LOG MODEL ---------------- #

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    service = Column(String, index=True)
    level = Column(String, index=True)
    message = Column(Text)
    raw_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    host = Column(String, nullable=True, index=True)
    pid = Column(Integer, nullable=True, index=True)
    ip_address = Column(String, nullable=True, index=True)
    status_code = Column(Integer, nullable=True, index=True)

    trace_id = Column(String, nullable=True, index=True)

# ---------------- INCIDENT MODEL ---------------- #

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    severity = Column(String(20), default="MEDIUM")
    status = Column(String(20), default="open")

    error_count = Column(Integer, default=0)

    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)

class IncidentReasoning(Base):
    __tablename__ = "incident_reasoning"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), unique=True)
    ai_summary = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    severity_score = Column(Integer, nullable=True)
    severity_level = Column(String(20), nullable=True)
    keywords = Column(JSON, nullable=True)
    recommended_actions = Column(JSON, nullable=True)
    raw_ai_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------- RUNBOOK MODEL ---------------- #

class Runbook(Base):
    __tablename__ = "runbooks"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(100), index=True, nullable=True)    
    error_type = Column(String(100), index=True, nullable=True) 
    name = Column(String(100), unique=True, index=True, nullable=True)
    title = Column(String(200), nullable=True)
    content = Column(Text)  # markdown content
    tags = Column(JSON, nullable=True)  # keywords for matching
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 