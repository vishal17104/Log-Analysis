import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict

# -----------------------------
# API CONFIG
# -----------------------------

BASE_URL = "http://127.0.0.1:8000"
LOG_ENDPOINT = f"{BASE_URL}/logs"

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
        "timestamp": datetime.utcnow().isoformat() + "Z",
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

def generate_logs(n: int = 100) -> List[Dict]:
    """Generate logs spread across last 15 minutes"""

    logs = []
    now = datetime.utcnow()

    for _ in range(n):

        log = generate_valid_log()

        log["timestamp"] = (
            now - timedelta(seconds=random.randint(0, 900))
        ).isoformat() + "Z"

        if random.random() < 0.2:
            log["level"] = "ERROR"

        logs.append(log)

    return logs


# -----------------------------
# CHAOS INJECTOR
# -----------------------------

def inject_chaos(logs: List[Dict], error_count: int = 20) -> List[Dict]:

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
# API SENDER
# -----------------------------

def send_logs_to_api(logs: List[Dict]):

    try:
        response = requests.post(LOG_ENDPOINT, json=logs, timeout=5)

        if response.status_code in [200, 201]:
            print(f"✅ Successfully sent {len(logs)} logs")
            return True

        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {LOG_ENDPOINT}")
        print("Make sure FastAPI is running!")
        return False

    except Exception as e:
        print(f"❌ Error sending logs: {e}")
        return False


# -----------------------------
# TRAFFIC SCENARIOS
# -----------------------------

def send_error_burst():

    print("🔥 Generating error burst...")

    logs = generate_logs(100)

    for i in range(80):
        logs[i]["level"] = "ERROR"

    send_logs_to_api(logs)


def send_normal_traffic():

    print("📊 Generating normal traffic...")

    logs = generate_logs(50)

    send_logs_to_api(logs)


def send_custom_batch():

    try:
        size = int(input("Batch size: "))
        error_pct = float(input("Error percentage (0-100): ")) / 100

        logs = generate_logs(size)

        error_count = int(size * error_pct)

        for i in range(error_count):
            logs[i]["level"] = "ERROR"

        send_logs_to_api(logs)

    except ValueError:
        print("❌ Invalid input")


# -----------------------------
# MAIN MENU
# -----------------------------

if __name__ == "__main__":

    print("\n" + "=" * 50)
    print("🚀 MOCK LOG GENERATOR")
    print("=" * 50)

    print("1. Generate error burst (100 logs)")
    print("2. Generate normal traffic (50 logs)")
    print("3. Generate custom batch")
    print("4. Show sample logs")
    print("5. Exit")

    print("-" * 50)

    while True:

        choice = input("\nChoose (1/2/3/4/5): ").strip()

        if choice == "1":
            send_error_burst()

        elif choice == "2":
            send_normal_traffic()

        elif choice == "3":
            send_custom_batch()

        elif choice == "4":

            print("\n===== VALID LOG SAMPLE =====")

            for log in generate_logs(5):
                print(log)

            print("\n===== CHAOS LOG SAMPLE =====")

            for log in inject_chaos([], 5):
                print(log)

        elif choice == "5":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice")