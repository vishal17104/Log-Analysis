from datetime import datetime

from database import SessionLocal
from models import Log
from mock_data import generate_logs


def seed_logs():
    db = SessionLocal()

    try:
        logs = generate_logs(1000)

        for log in logs:
            # Extract only DB-supported fields
            db_log = Log(
                timestamp=datetime.fromisoformat(log["timestamp"]),
                service=log["service"],
                level=log["level"],
                message=log["message"],

                # Store extra fields safely as JSON
                raw_data={
                    k: v for k, v in log.items()
                    if k not in {"timestamp", "service", "level", "message"}
                }
            )
            db.add(db_log)

        db.commit()
        print("✅ Successfully inserted 1000 logs into database")

    except Exception as e:
        db.rollback()
        print("❌ Error inserting logs:", e)

    finally:
        db.close()


if __name__ == "__main__":
    seed_logs()
