import requests
import streamlit as st 
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

def generate_error_burst():
    """Generate 100 logs with 80% errors"""
    try:
        response = requests.post(f"{BASE_URL}/generate/error-burst", timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Failed to generate error burst: {e}")
        return None

def generate_normal_traffic():
    """Generate 50 normal logs"""
    try:
        response = requests.post(f"{BASE_URL}/generate/normal-traffic", timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Failed to generate normal traffic: {e}")
        return None

def generate_custom_batch(batch_size: int, error_burst: bool = True, service: str = None):
    """Generate custom batch of logs"""
    try:
        payload = {
            "batch_size": batch_size,
            "error_burst": error_burst,
            "auto_detect": True
        }
        if service:
            payload["service"] = service
        
        response = requests.post(f"{BASE_URL}/generate/logs", json=payload, timeout=15)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Failed to generate custom batch: {e}")
        return None