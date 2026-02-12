from sqlalchemy.orm import session
from sqlalchemy import func
from datetime import datetime, timedelta
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

def get_log_stats(db: session, minutes: int = 60):
    """Get log statistics for last N minutes"""
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)

    level_counts = db.query(models.Log.level, func.count().label('count')).filter(models.Log.timestamp >= cutoff).group_by(models.Log.level).all()

    service_counts = db.query(models.Log.service, func.count().label('count')).filter(models.Log.timestamp >= cutoff).group_by(models.Log.service).all()

    timeline = db.query(func.date_trunc('minute', models.Log.timestamp).label('minute'), func.count().label('count')).filter(models.Log.level == 'ERROR',models.Log.timestamp >= cutoff).group_by('minute').order_by('minute').all()

    return {
        "total_logs": sum(c for _, c in level_counts),
        "error_count": next((c for l, c in level_counts if l == 'ERROR'), 0),
        "warn_count": next((c for l, c in level_counts if l == 'WARN'), 0),
        "info_count": next((c for l, c in level_counts if l == 'INFO'), 0),
        "debug_count": next((c for l, c in level_counts if l == 'DEBUG'), 0),
        "by_service": {s: c for s, c in service_counts},
        "timeline": [{"minute": m, "count": c} for m, c in timeline],
        "time_range": {
            "start": cutoff,
            "end": datetime.utcnow()
        }
    }

