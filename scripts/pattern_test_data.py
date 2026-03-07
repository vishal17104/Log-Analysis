import requests
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8001/logs"


def send_logs(logs):
    r = requests.post(BASE_URL, json=logs)
    print("Sent", len(logs), "logs")


def db_connection_pattern():
    logs = []
    for _ in range(10):
        logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "database",
            "level": "ERROR",
            "message": "dial tcp connection refused"
        })
    return logs


def api_rate_limit_pattern():
    logs = []
    for _ in range(10):
        logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "api",
            "level": "ERROR",
            "message": "429 too many requests"
        })
    return logs


def memory_leak_pattern():
    logs = []
    for _ in range(10):
        logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "worker",
            "level": "ERROR",
            "message": "out of memory heap allocation failure"
        })
    return logs


def menu():

    while True:

        print("\nPattern Test Generator")
        print("1. DB connection pattern")
        print("2. API rate limit pattern")
        print("3. Memory leak pattern")
        print("4. Exit")

        c = input("Choose: ")

        if c == "1":
            send_logs(db_connection_pattern())

        elif c == "2":
            send_logs(api_rate_limit_pattern())

        elif c == "3":
            send_logs(memory_leak_pattern())

        elif c == "4":
            break


if __name__ == "__main__":
    menu()