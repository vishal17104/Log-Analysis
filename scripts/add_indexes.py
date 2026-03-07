from backend.database import engine
from sqlalchemy import inspect, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_indexes():
    """Add missing indexes to database"""

    inspector = inspect(engine)
    existing_indexes = inspector.get_indexes("logs")
    existing_names = [idx["name"] for idx in existing_indexes]

    logger.info(f"Found {len(existing_indexes)} existing indexes on logs table")

    indexes_to_add = [
        {
            "name": "ix_logs_timestamp_level",
            "columns": ["timestamp", "level"],
            "unique": False,
        },
        {
            "name": "ix_logs_timestamp_service",
            "columns": ["timestamp", "service"],
            "unique": False,
        },
        {
            "name": "ix_logs_service_level_timestamp",
            "columns": ["service", "level", "timestamp"],
            "unique": False,
        },
        {
            "name": "ix_logs_level_processed",
            "columns": ["level", "processed"],
            "unique": False,
        },
    ]

    with engine.begin() as conn:
        for idx in indexes_to_add:

            if idx["name"] not in existing_names:

                logger.info(f"Adding index {idx['name']}...")

                columns = ", ".join(idx["columns"])
                unique = "UNIQUE " if idx["unique"] else ""

                conn.execute(
                    text(
                        f"CREATE {unique}INDEX IF NOT EXISTS {idx['name']} "
                        f"ON logs ({columns})"
                    )
                )

                logger.info(f"Added {idx['name']}")

            else:
                logger.info(f"Index {idx['name']} already exists")

    logger.info("Index migration complete")


if __name__ == "__main__":
    add_indexes()