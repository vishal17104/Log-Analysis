import streamlit as st
from streamlit_autorefresh import st_autorefresh
from api_client import get_incidents
from charts import severity_chart, service_chart
from incident_view import show_incident_detail


st.title("🤖 AI Log Monitoring Dashboard")

st_autorefresh(interval=15000, key="dashboardrefresh")

incidents = get_incidents()

if not incidents:
    st.warning("No incidents available. Ensure backend is running.")
    st.stop()


st.subheader("📋 Recent Incidents")

for inc in incidents[:10]:

    st.write(
        f"ID: {inc['id']} | {inc['title']} | Severity: {inc['severity']} | Status: {inc['status']}"
    )


severity_chart(incidents)

service_chart(incidents)


st.subheader("🔍 Investigate Incident")

incident_options = {
    f"ID {i['id']} - {i['title']}": i["id"] for i in incidents
}

selected_label = st.selectbox(
    "Select an incident",
    options=list(incident_options.keys())
)

if selected_label:

    show_incident_detail(
        incident_options[selected_label]
    )