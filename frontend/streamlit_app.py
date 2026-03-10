import streamlit as st
import pandas as pd
from log_feed import render_log_feed
from streamlit_autorefresh import st_autorefresh
from api_client import get_stats, get_incidents, get_logs
from charts import render_error_frequency, render_severity_distribution
from incident_view import render_incident_list


# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Sentinel AI Monitoring",
    layout="wide",
    initial_sidebar_state="expanded"
)

st_autorefresh(interval=5000, key="sentinel_refresh")


# ---------------- DARK THEME CSS ---------------- #

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }

    h1, h2, h3, h4, p {
        color: white !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0e1117 !important;
        border-right: 1px solid #1e2130;
    }

    div[data-testid="stMetric"] {
        background-color: #1e2130;
        border: 1px solid #2d313e;
        border-radius: 12px;
        padding: 20px !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #808495 !important;
        font-size: 13px !important;
    }

    div[data-testid="stMetricValue"] {
        color: white !important;
        font-size: 30px !important;
    }

    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- SIDEBAR ---------------- #

st.sidebar.markdown(
    "<h2 style='color:#00d1ff;'>🛡️ Sentinel AI</h2>",
    unsafe_allow_html=True
)

menu = st.sidebar.radio(
    "Navigation",
    ["System Dashboard", "Active Incidents", "Logs Explorer", "Settings"]
)


# ---------------- DATA FETCHING ---------------- #

stats = get_stats()
incidents = get_incidents()


# ---------------- SYSTEM DASHBOARD ---------------- #

if menu == "System Dashboard":

    st.markdown("<h1>System Monitoring Dashboard</h1>", unsafe_allow_html=True)
    st.write("Real-time operational visibility for platform reliability.")

    # ---------- METRICS ROW ----------

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Active Incidents",
        len(incidents)
    )

    m2.metric(
        "Total Logs",
        stats.get("total_logs", 0)
    )

    m3.metric(
        "Error Logs",
        stats.get("error_count", 0)
    )

    m4.metric(
        "Warning Logs",
        stats.get("warning_count", 0)
    )

    st.write("")

    # ---------- CHARTS ----------

    col1, col2 = st.columns(2)

    with col1:
        render_error_frequency(stats)

    with col2:
        render_severity_distribution(incidents)

    # ---------- LIVE LOG FEED ----------

    st.divider()
    render_log_feed()


# ---------------- INCIDENT PAGE ---------------- #

elif menu == "Active Incidents":

    render_incident_list(incidents)


# ---------------- LOGS EXPLORER ---------------- #

elif menu == "Logs Explorer":

    st.markdown("<h1>Logs Explorer</h1>", unsafe_allow_html=True)
    st.write("Search through system logs in real time.")

    search_query = st.text_input("Search Logs (Service or Message)")

    logs = get_logs(limit=100)

    if logs:

        df = pd.DataFrame(logs)

        if search_query:
            df = df[
                df['message'].str.contains(search_query, case=False) |
                df['service'].str.contains(search_query, case=False)
            ]

        st.dataframe(df, use_container_width=True)

    else:
        st.info("No logs found. Ensure backend is running and data is generated.")


# ---------------- SETTINGS ---------------- #

elif menu == "Settings":

    st.markdown("<h1>System Settings</h1>", unsafe_allow_html=True)
    st.write("Configuration and integrations.")

    with st.expander("API Configuration"):
        st.write("Backend URL: `http://localhost:8000` (Default)")
        st.write("Status: 🟢 Connected" if stats else "Status: 🔴 Disconnected")

    with st.expander("AI Integration"):
        st.write("Model: `Gemini 1.5 Flash`")
        st.write("Purpose: Automated Triage & Recommendation")