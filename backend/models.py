from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


Base = declarative_base()

#database models for log, incident and runbook

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



class Incident(Base):

    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    severity = Column(String(20), default="MEDIUM")
    status = Column(String(20), default="open")
    error_count = Column(Integer, default=0)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class Runbook(Base):
    __tablename__ = "runbooks"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    content = Column(Text)