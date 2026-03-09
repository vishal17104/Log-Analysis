import asyncio
import logging
from backend.database import SessionLocal
from backend import models
from backend.routers.ws_logs import manager

logger = logging.getLogger(__name__)


class LogBroadcaster:
    """Broadcast new logs to all connected clients"""

    def __init__(self):
        self.running = False
        self.last_id = 0

    async def start(self):
        """Start polling database for new logs"""
        self.running = True
        logger.info("Log broadcaster started")

        while self.running:
            try:
                await self.check_new_logs()
            except Exception as e:
                logger.error(f"Error checking new logs: {e}")

            await asyncio.sleep(1)

    async def stop(self):
        """Stop broadcaster"""
        self.running = False
        logger.info("Log broadcaster stopped")

    async def check_new_logs(self):
        """Fetch logs newer than last_id and broadcast"""
        db = SessionLocal()

        try:
            new_logs = (
                db.query(models.Log)
                .filter(models.Log.id > self.last_id)
                .order_by(models.Log.id)
                .limit(100)
                .all()
            )

            for log in new_logs:
                log_data = {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "service": log.service or "unknown",
                    "level": log.level,
                    "message": log.message[:100] if log.message else "",
                    "host": log.host,
                }

                await manager.broadcast({
                    "type": "new_log",
                    "data": log_data
                })

                if log.id > self.last_id:
                    self.last_id = log.id

        except Exception as e:
            logger.error(f"Error checking new logs: {e}")

        finally:
            db.close()

    def reset(self):
        """Reset log pointer"""
        self.last_id = 0
        logger.info("Log broadcaster reset")


broadcaster = LogBroadcaster()


async def start_broadcaster():
    """Start broadcaster in background"""
    asyncio.create_task(broadcaster.start())


def get_broadcaster():
    return broadcaster