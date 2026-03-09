# frontend/api_client.py
import requests
import streamlit as st

API_URL = "http://localhost:8000"

def check_api():
    """Check if API is reachable using root endpoint"""
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_logs():
    try:
        response = requests.get(f"{API_URL}/logs/", params={"limit": 10})
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_incidents():
    try:
        response = requests.get(f"{API_URL}/incidents/")
        return response.json() if response.status_code == 200 else []
    except:
        return []