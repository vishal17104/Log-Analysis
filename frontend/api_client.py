import requests
from config import API_URL


BASE_URL = API_URL

def get_incidents():
    try:
        r = requests.get(f"{BASE_URL}/incidents")
        r.raise_for_status()
        return r.json()
    except Exception:
        return []

def get_incident(incident_id):
    try:
        r = requests.get(f"{BASE_URL}/incidents/{incident_id}")
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

def get_recommendation(incident_id):
    try:
        r = requests.get(f"{BASE_URL}/recommendations/{incident_id}")
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def get_stats():
    """Fetches log statistics (error counts, service distribution) for the metrics row"""
    try:
        r = requests.get(f"{BASE_URL}/logs/stats?minutes=1440")
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

def get_logs(limit=50):
    """Fetches recent logs to populate the frequency charts"""
    try:
        r = requests.get(f"{BASE_URL}/logs?limit={limit}")
        r.raise_for_status()
        return r.json()
    except Exception:
        return []