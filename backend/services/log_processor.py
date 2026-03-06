import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend import models, crud, schemas
from backend.database import SessionLocal
from backend.services.notifier import notifier

logger = logging.getLogger(__name__)


class LogProcessor:
    """Async background log processor"""

    def __init__(self, batch_size: int = 100, interval_seconds: int = 10):
        self.batch_size = batch_size
        self.interval = interval_seconds
        self.running = False
        self.processed_count = 0
        self.callbacks = []

    async def start(self):
        """Start the background processor"""
        self.running = True

        logger.info(
            f"Log processor started (batch: {self.batch_size}, interval: {self.interval}s)"
        )

        while self.running:
            try:
                await self._process_batch()
            except Exception as e:
                logger.error(f"Error in log processor: {e}")

            await asyncio.sleep(self.interval)

    async def stop(self):
        """Stop processor"""
        self.running = False
        logger.info("Log processor stopped")

    async def _process_batch(self):
        """Process a batch of unprocessed logs"""

        db = SessionLocal()

        try:
            logs = (
                db.query(models.Log)
                .filter(models.Log.processed == False)
                .limit(self.batch_size)
                .all()
            )

            if not logs:
                return

            logger.info(f"Processing {len(logs)} new logs")

            # Group logs by service
            by_service: Dict[str, List[models.Log]] = {}

            for log in logs:
                by_service.setdefault(log.service, []).append(log)

            # Analyze errors
            for service, service_logs in by_service.items():

                error_count = sum(1 for l in service_logs if l.level == "ERROR")

                if error_count >= 5:

                    logger.info(
                        f"High error rate detected in {service}: {error_count} errors"
                    )

                    await self._check_for_incident(db, service)

            # Mark logs processed
            for log in logs:
                log.processed = True

            db.commit()

            self.processed_count += len(logs)

            # Notify websocket dashboard
            await self._notify_clients(
                {
                    "type": "batch_processed",
                    "count": len(logs),
                    "total_processed": self.processed_count,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        finally:
            db.close()

    async def _check_for_incident(self, db: Session, service: str):
        """Check for spike and create incident"""

        cutoff = datetime.utcnow() - timedelta(minutes=5)

        recent_errors = (
            db.query(models.Log)
            .filter(
                models.Log.service == service,
                models.Log.level == "ERROR",
                models.Log.timestamp >= cutoff,
            )
            .count()
        )

        if recent_errors < 10:
            return

        # Prevent duplicate incidents
        existing_incident = (
            db.query(models.Incident)
            .filter(
                models.Incident.service == service,
                models.Incident.status == "open",
            )
            .first()
        )

        if existing_incident:
            logger.info(f"Incident already open for {service}")
            return

        logger.info(f"🚨 Creating incident for {service}")

        incident_data = {
            "title": f"Error spike in {service} service",
            "service": service,
            "severity": "HIGH" if recent_errors > 20 else "MEDIUM",
            "error_count": recent_errors,
            "window_start": cutoff,
            "window_end": datetime.utcnow(),
        }

        # Convert dict → schema
        incident_schema = schemas.IncidentCreate(**incident_data)

        # Create incident
        incident = crud.create_incident(db, incident_schema)

        # 🔔 TRIGGER NOTIFICATIONS (THIS WAS MISSING)
        notifier.send_all(incident)

        # Notify websocket clients
        await self._notify_clients(
            {
                "type": "incident_created",
                "service": service,
                "incident_id": incident.id,
                "error_count": recent_errors,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def register_callback(self, callback):
        """Register websocket callback"""
        self.callbacks.append(callback)

    async def _notify_clients(self, data: Dict[str, Any]):
        """Notify websocket clients"""

        for callback in self.callbacks:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Callback error: {e}")


processor = LogProcessor()


async def start_processor():
    """Start processor from FastAPI startup"""
    asyncio.create_task(processor.start())


def get_processor():
    """Return processor instance"""
    return processor