import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional


# -----------------------------
# SCHEMA-CONSTRAINED CONSTANTS
# -----------------------------

SERVICES = ["payment", "auth", "api", "worker", "frontend", "database"]
LEVELS = ["INFO", "WARNING", "ERROR"]

HOSTS = ["server-1", "server-2", "server-3"]
IPS = ["10.0.0.1", "10.0.0.2", "192.168.1.10"]


# -----------------------------
# VALID LOG GENERATOR
# -----------------------------

def generate_valid_log() -> Dict:
    """
    Generates a log that STRICTLY conforms to LogCreate schema.
    """
    log = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": random.choice(SERVICES),
        "level": random.choice(LEVELS),
        "message": random.choice([
            "Request processed successfully",
            "Database connection failed",
            "Timeout while calling external API",
            "User authentication failed",
            "Worker process crashed"
        ])
    }

    # Optional fields (randomly included)
    if random.random() < 0.5:
        log["host"] = random.choice(HOSTS)

    if random.random() < 0.4:
        log["pid"] = random.randint(100, 5000)

    if random.random() < 0.4:
        log["ip_address"] = random.choice(IPS)

    if random.random() < 0.3:
        log["status_code"] = random.choice([200, 400, 401, 403, 500])

    if random.random() < 0.3:
        log["trace_id"] = f"trace-{random.randint(100000, 999999)}"

    return log


# -----------------------------
# BULK LOG GENERATOR
# -----------------------------

def generate_logs(n: int = 1000) -> List[Dict]:
    """
    Generates n valid logs.
    - Timestamps spread over last 15 minutes
    - ~20% ERROR logs
    """
    logs = []
    now = datetime.utcnow()

    for _ in range(n):
        log = generate_valid_log()

        log["timestamp"] = (
            now - timedelta(seconds=random.randint(0, 900))
        ).isoformat()

        if random.random() < 0.2:
            log["level"] = "ERROR"

        logs.append(log)

    return logs


# -----------------------------
# CHAOS INJECTOR
# -----------------------------

def inject_chaos(logs: List[Dict], error_count: int = 50) -> List[Dict]:
    """
    Generates logs that MUST FAIL Pydantic validation.
    Each log violates the schema in a different way.
    """
    chaos_logs = []

    for _ in range(error_count):
        chaos_type = random.choice([
            "missing_required",
            "wrong_type",
            "invalid_enum",
            "invalid_service",
            "empty_message",
            "oversized_message",
            "malformed_object"
        ])

        log = generate_valid_log()

        if chaos_type == "missing_required":
            log.pop("service")

        elif chaos_type == "wrong_type":
            log["pid"] = "not-an-int"

        elif chaos_type == "invalid_enum":
            log["level"] = "CRITICAL"

        elif chaos_type == "invalid_service":
            log["service"] = "billing"

        elif chaos_type == "empty_message":
            log["message"] = ""

        elif chaos_type == "oversized_message":
            log["message"] = "x" * 600

        elif chaos_type == "malformed_object":
            log = {"broken": True}

        chaos_logs.append(log)

    return chaos_logs


# -----------------------------
# LOCAL TEST RUNNER
# -----------------------------

if __name__ == "__main__":
    valid_logs = generate_logs(1000)
    chaos_logs = inject_chaos(valid_logs, 50)

    print("===== VALID LOG SAMPLE =====")
    for log in valid_logs[:5]:
        print(log)

    print("\n===== CHAOS LOG SAMPLE =====")
    for log in chaos_logs[:5]:
        print(log)
