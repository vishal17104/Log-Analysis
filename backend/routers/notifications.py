from fastapi import APIRouter, Depends, HTTPException
from backend.services.notifier import notifier
from backend import crud
from sqlalchemy.orm import Session
from backend.database import get_db

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/test")
def test_notifications():
    """Send a test notification to verify all channels are working"""
    try:
        # Create a dummy incident for testing
        class DummyIncident:
            def __init__(self):
                self.id = 999
                self.service = "test-service"
                self.severity = "TEST"
                self.error_count = 42
                self.title = "Test notification incident"
        
        dummy = DummyIncident()
        notifier.send_all(dummy)
        
        return {
            "message": "Test notifications sent successfully",
            "channels": ["console", "file", "email"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification failed: {str(e)}")

@router.post("/incident/{incident_id}")
def notify_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """Manually trigger notifications for an existing incident"""
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        notifier.send_all(incident)
        return {
            "message": f"Notifications sent for incident #{incident_id}",
            "incident_id": incident_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification failed: {str(e)}")

@router.get("/status")
def notification_status():
    """Check which notification channels are configured"""
    return {
        "console": True,
        "file": True,
        "email": False,
        "log_file": "alerts.log"
    }