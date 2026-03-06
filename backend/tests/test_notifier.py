from backend.services.notifier import notifier

class FakeIncident:
    id = 1
    service = "payment"
    severity = "HIGH"
    error_count = 25
    title = "Error spike in payment service"

incident = FakeIncident()

notifier.send_all(incident)