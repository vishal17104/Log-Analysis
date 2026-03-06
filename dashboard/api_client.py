import requests

BASE_URL = "http://localhost:8000"


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