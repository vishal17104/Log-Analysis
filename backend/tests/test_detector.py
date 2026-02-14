import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine
from backend import models
from backend.detector import detect_and_create_incidents


# ---------------- FIXTURES ----------------

@pytest.fixture(scope="function")
def db():
    """
    Provides a clean database session for each test using transaction rollback.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    # Clean tables before test
    session.query(models.Incident).delete()
    session.query(models.Log).delete()
    session.commit()

    yield session  # test runs here

    session.close()
    transaction.rollback()
    connection.close()


# ---------------- TESTS ----------------

def test_no_errors_no_incident(db: Session):
    """
    No ERROR logs → no incidents should be created.
    """
    detect_and_create_incidents(db)

    incidents = db.query(models.Incident).all()
    assert len(incidents) == 0


def test_single_minute_error_spike_no_incident(db: Session):
    """
    Errors in only ONE minute → no incident
    (detector requires consecutive minutes).
    """
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    for _ in range(15):  # above ERROR_THRESHOLD = 10
        db.add(models.Log(
            service="auth-service",
            level="ERROR",
            timestamp=now,
            message="Test error"
        ))

    db.commit()

    detect_and_create_incidents(db)

    incidents = db.query(models.Incident).all()
    assert len(incidents) == 0


def test_consecutive_error_spikes_create_incident(db: Session):
    """
    Errors above threshold in 2 consecutive minutes → incident created.
    """
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    # Previous minute
    for _ in range(15):
        db.add(models.Log(
            service="auth-service",
            level="ERROR",
            timestamp=now - timedelta(minutes=1),
            message="Old error"
        ))

    # Current minute
    for _ in range(15):
        db.add(models.Log(
            service="auth-service",
            level="ERROR",
            timestamp=now,
            message="Current error"
        ))

    db.commit()

    detect_and_create_incidents(db)

    incidents = db.query(models.Incident).all()
    assert len(incidents) == 1
    assert "auth-service" in incidents[0].title
    assert incidents[0].severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_duplicate_incident_not_created(db: Session):
    """
    If an open incident already exists, detector should not create another.
    """
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    for minute_offset in [0, 1]:
        for _ in range(15):
            db.add(models.Log(
                service="payment-service",
                level="ERROR",
                timestamp=now - timedelta(minutes=minute_offset),
                message="Persistent error"
            ))

    db.commit()

    # First run → creates incident
    detect_and_create_incidents(db)

    # Second run → should NOT create another
    detect_and_create_incidents(db)

    incidents = db.query(models.Incident).all()
    assert len(incidents) == 1
