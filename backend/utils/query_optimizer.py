import time
import logging
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from backend import models

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Helper class to benchmark and analyze database queries"""

    def __init__(self, db: Session):
        self.db = db

    def benchmark_query(self, query_func, *args, **kwargs):
        """Measure execution time of a query"""
        start = time.perf_counter()
        result = query_func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        return result, elapsed

    def analyze_query_plan(self, query):
        """Get EXPLAIN ANALYZE query plan"""
        try:
            sql = str(
                query.statement.compile(
                    self.db.bind,
                    compile_kwargs={"literal_binds": True},
                )
            )

            explain = self.db.execute(text(f"EXPLAIN ANALYZE {sql}")).fetchall()

            return "\n".join([row[0] for row in explain])

        except Exception as e:
            logger.error(f"Failed to get query plan: {e}")
            return None

    def vacuum_analyze(self):
        """Run VACUUM ANALYZE to update DB statistics"""
        try:
            conn = self.db.connection()
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text("VACUUM ANALYZE"))
            logger.info("VACUUM ANALYZE completed")
            return True

        except Exception as e:
            logger.error(f"VACUUM ANALYZE failed: {e}")
            return False


# Optimized Query Functions


def get_recent_errors(db: Session, minutes: int = 5):
    """Get recent ERROR logs"""
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)

    return db.query(models.Log).filter(
        models.Log.level == "ERROR",
        models.Log.timestamp >= cutoff,
    ).all()


def get_error_stats(db: Session, minutes: int = 60):
    """Return error counts per service"""
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)

    stats = (
        db.query(
            models.Log.service,
            func.count().label("count"),
        )
        .filter(
            models.Log.level == "ERROR",
            models.Log.timestamp >= cutoff,
        )
        .group_by(models.Log.service)
        .all()
    )

    return {service: count for service, count in stats}


def get_incident_stats(db: Session, days: int = 7):
    """Return incident statistics"""
    cutoff = datetime.utcnow() - timedelta(days=days)

    open_incidents = (
        db.query(models.Incident)
        .filter(
            models.Incident.status == "open",
            models.Incident.detected_at >= cutoff,
        )
        .count()
    )

    by_severity = (
        db.query(
            models.Incident.severity,
            func.count().label("count"),
        )
        .filter(
            models.Incident.detected_at >= cutoff,
        )
        .group_by(models.Incident.severity)
        .all()
    )

    return {
        "open_count": open_incidents,
        "by_severity": {s: c for s, c in by_severity},
    }


def search_logs(db: Session, search_term: str, limit: int = 50):
    """Search logs using full-text search with fallback"""

    try:
        result = (
            db.query(models.Log)
            .filter(
                models.Log.message.op("@@")(
                    func.plainto_tsquery("english", search_term)
                )
            )
            .order_by(models.Log.timestamp.desc())
            .limit(limit)
            .all()
        )

        if result:
            return result

    except Exception as e:
        logger.warning(f"Full text search failed, using fallback: {e}")

    return (
        db.query(models.Log)
        .filter(models.Log.message.ilike(f"%{search_term}%"))
        .order_by(models.Log.timestamp.desc())
        .limit(limit)
        .all()
    )