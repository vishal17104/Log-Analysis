# backend/services/mock_generator.py
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend import models

# Configuration
SERVICES = ["payment", "auth", "api", "worker", "frontend", "database"]
LEVELS = ["INFO", "WARNING", "ERROR"]  # 3 levels
HOSTS = ["server-1", "server-2", "server-3"]
IPS = ["10.0.0.1", "10.0.0.2", "192.168.1.10"]

# Weight for each level (must match number of LEVELS!)
LEVEL_WEIGHTS = [0.7, 0.15, 0.15]  # INFO=70%, WARNING=15%, ERROR=15%

# Error messages by service
ERROR_MESSAGES = {
    'payment': [
        "Database connection timeout",
        "Payment gateway timeout",
        "Insufficient funds",
        "Invalid card number",
        "Transaction failed",
        "Credit card declined"
    ],
    'auth': [
        "Invalid credentials",
        "Token expired",
        "User not found",
        "Rate limit exceeded",
        "Session invalid"
    ],
    'api': [
        "Internal server error",
        "Bad request",
        "Resource not found",
        "Method not allowed",
        "Validation failed"
    ],
    'database': [
        "Connection refused",
        "Deadlock detected",
        "Query timeout",
        "Too many connections",
        "Disk full"
    ],
    'worker': [
        "Job processing failed",
        "Queue full",
        "Memory limit exceeded",
        "Task timed out"
    ],
    'frontend': [
        "API call failed",
        "Rendering error",
        "Asset not found",
        "WebSocket disconnected"
    ]
}

def generate_single_log(service: str = None, force_error: bool = False) -> Dict[str, Any]:
    """Generate a single realistic log entry"""
    
    if not service:
        service = random.choice(SERVICES)
    
    if force_error:
        level = 'ERROR'
    else:
        # Now weights match LEVELS (3 items, 3 weights)
        level = random.choices(LEVELS, weights=LEVEL_WEIGHTS)[0]
    
    if level == 'ERROR' and service in ERROR_MESSAGES:
        message = random.choice(ERROR_MESSAGES[service])
    elif level == 'WARNING':
        message = random.choice([
            "High memory usage",
            "Slow query detected",
            "Retrying failed operation",
            "Cache miss ratio high"
        ])
    else:
        message = random.choice([
            "Request processed successfully",
            "User logged in",
            "Payment completed",
            "Cache updated",
            "Background job completed"
        ])
    
    return {
        "service": service,
        "level": level,
        "message": message,
        "timestamp": (datetime.utcnow() - timedelta(seconds=random.randint(0, 3600))).isoformat() + "Z",
        "host": random.choice(HOSTS),
        "pid": random.randint(1000, 9999),
        "ip_address": random.choice(IPS),
        "status_code": 200 if level != 'ERROR' else random.choice([400, 404, 500, 502, 503, 504])
    }

def generate_log_batch(batch_size: int = 100, error_burst: bool = False) -> List[Dict[str, Any]]:
    """Generate a batch of logs"""
    logs = []
    for i in range(batch_size):
        if error_burst and i < batch_size * 0.8:
            log = generate_single_log(force_error=True)
        else:
            log = generate_single_log()
        logs.append(log)
    return logs

def insert_logs_batch(db: Session, logs: List[Dict[str, Any]]) -> int:
    """Insert logs directly into database (bypasses API)"""
    db_logs = []
    for log in logs:
        db_log = models.Log(
            service=log["service"],
            level=log["level"],
            message=log["message"],
            timestamp=datetime.fromisoformat(log["timestamp"].replace('Z', '+00:00')),
            host=log.get("host"),
            pid=log.get("pid"),
            ip_address=log.get("ip_address"),
            status_code=log.get("status_code"),
            raw_data=log
        )
        db.add(db_log)
        db_logs.append(db_log)
    
    db.commit()
    return len(db_logs)