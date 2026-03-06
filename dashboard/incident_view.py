import streamlit as st
from api_client import get_incident, get_recommendation


def show_incident_detail(incident_id):

    incident = get_incident(incident_id)

    if not incident:
        st.error("Incident not found.")
        return

    st.subheader("🚨 Incident Details")

    st.json(incident)

    recommendation = get_recommendation(incident_id)

    st.subheader("🧠 Recommended Solution")

    if recommendation:
        st.json(recommendation)
    else:
        st.info("No recommendation available yet.")