from sqlalchemy.orm import session
from datetime import datetime
from backend import models

#creating log
def create_log(db: session, service: str, level: str, message: str):
    db_log = models.Log(
        service=service,
        level=level,
        message=message,
        timestamp=datetime.utcnow()
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

#getting logs
def get_logs(db: session,  skip: int = 0, limit: int = 50):
    return db.query(models.Log).order_by(models.Log.timestamp.desc()).limit(limit).all()