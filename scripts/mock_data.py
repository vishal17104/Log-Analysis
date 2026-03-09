import random
import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict

# -----------------------------
# API CONFIG
# -----------------------------

BASE_URL = "http://127.0.0.1:8000"
LOG_ENDPOINT = f"{BASE_URL}/logs/" # Matches your FastAPI router

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
    """Generate a single valid log matching LogCreate schema"""
    log = {
        # Using modern timezone-aware UTC
        "timestamp": datetime.now(timezone.utc).isoformat(),
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

    if random.random() < 0.5: log["host"] = random.choice(HOSTS)
    if random.random() < 0.4: log["pid"] = random.randint(100, 5000)
    if random.random() < 0.4: log["ip_address"] = random.choice(IPS)
    if random.random() < 0.3: log["status_code"] = random.choice([200, 400, 401, 403, 500])
    if random.random() < 0.3: log["trace_id"] = f"trace-{random.randint(100000, 999999)}"

    return log

def generate_logs(n: int = 100) -> List[Dict]:
    logs = []
    now = datetime.now(timezone.utc)
    for _ in range(n):
        log = generate_valid_log()
        log["timestamp"] = (now - timedelta(seconds=random.randint(0, 900))).isoformat()
        if random.random() < 0.2: log["level"] = "ERROR"
        logs.append(log)
    return logs

# -----------------------------
# API SENDER
# -----------------------------

def send_logs_to_api(logs: List[Dict]):
    try:
        # Note: If your router expects a list, send the list directly
        response = requests.post(LOG_ENDPOINT, json=logs, timeout=5)
        if response.status_code in [200, 201]:
            print(f"✅ Successfully sent {len(logs)} logs")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return False

# -----------------------------
# TRAFFIC SCENARIOS
# -----------------------------

def send_error_burst():
    print("🔥 Generating error burst...")
    logs = generate_logs(100)
    for i in range(80): logs[i]["level"] = "ERROR"
    send_logs_to_api(logs)

def send_normal_traffic():
    print("📊 Generating normal traffic...")
    logs = generate_logs(50)
    send_logs_to_api(logs)

if __name__ == "__main__":
    print("\n🚀 MOCK LOG GENERATOR STARTED")
    # Simple Menu Logic
    send_normal_traffic()