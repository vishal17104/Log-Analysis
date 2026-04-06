# frontend/streamlit_app.py
import streamlit as st
import pandas as pd
import requests
from log_feed import render_log_feed
from streamlit_autorefresh import st_autorefresh
from api_client import (
    get_stats, 
    get_incidents, 
    get_logs,
    generate_error_burst,
    generate_normal_traffic,
    generate_custom_batch
)
from charts import render_error_frequency, render_severity_distribution
from incident_view import render_incident_list
from agent_control import render_agent_control
from runbook_editor import render_runbook_editor
from analytics import render_analytics 

# ============ IMPORT FROM CONFIG ============
from config import (
    APP_TITLE,
    APP_ICON,
    PAGE_TITLE,
    LAYOUT,
    AUTO_REFRESH_INTERVAL,
    ENABLE_AUTO_REFRESH,
    PRIMARY_COLOR,
    BACKGROUND_COLOR,
    CARD_COLOR,
    THEME,
    API_URL
)

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# ---------------- DARK THEME CSS WITH CONFIG COLORS ---------------- #

st.markdown(f"""
<style>
    .stApp {{ background-color: {BACKGROUND_COLOR}; }}

    h1, h2, h3, h4, p {{
        color: white !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {BACKGROUND_COLOR} !important;
        border-right: 1px solid #1e2130;
    }}

    div[data-testid="stMetric"] {{
        background-color: {CARD_COLOR};
        border: 1px solid #2d313e;
        border-radius: 12px;
        padding: 20px !important;
    }}

    div[data-testid="stMetricLabel"] {{
        color: #808495 !important;
        font-size: 13px !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: white !important;
        font-size: 30px !important;
    }}

    .block-container {{
        padding-top: 2rem;
    }}

    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: #0e1117;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
    }}

    /* Optional: Add theme-based adjustments */
    {'' if THEME == 'dark' else '''
    .stApp { background-color: #ffffff; }
    h1, h2, h3, h4, p { color: #000000 !important; }
    '''}
</style>
""", unsafe_allow_html=True)


# ---------------- SIDEBAR ---------------- #

st.sidebar.markdown(
    f"<h2 style='color:{PRIMARY_COLOR};'>🛡️ {APP_TITLE}</h2>",
    unsafe_allow_html=True
)

menu = st.sidebar.radio(
    "Navigation",
    [
        "System Dashboard",
        "Active Incidents",
        "Logs Explorer",
        "Agent Control",
        "Runbooks",
        "Analytics",
        "Test Data",   # ← NEW
        "Settings"
    ]
)


# ---------------- CACHED DATA ---------------- #

@st.cache_data(ttl=5)
def load_stats():
    return get_stats()

@st.cache_data(ttl=5)
def load_incidents():
    return get_incidents()


stats = load_stats()
incidents = load_incidents()


# ---------------- SYSTEM DASHBOARD ---------------- #

if menu == "System Dashboard":

    if ENABLE_AUTO_REFRESH:
        st_autorefresh(interval=AUTO_REFRESH_INTERVAL, key="dashboard_refresh")

    st.markdown("<h1>System Monitoring Dashboard</h1>", unsafe_allow_html=True)
    st.write("Real-time operational visibility for platform reliability.")

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Active Incidents", len(incidents))
    m2.metric("Total Logs", stats.get("total_logs", 0))
    m3.metric("Error Logs", stats.get("error_count", 0))
    m4.metric("Warning Logs", stats.get("warning_count", 0))

    st.write("")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        render_error_frequency(stats)

    with col2:
        render_severity_distribution(incidents)

    st.divider()

    render_log_feed()


# ---------------- ACTIVE INCIDENTS PAGE ---------------- #

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


# ---------------- AGENT CONTROL ---------------- #

elif menu == "Agent Control":

    render_agent_control()


# ---------------- RUNBOOKS ---------------- #

elif menu == "Runbooks":

    render_runbook_editor()


# ---------------- ANALYTICS ---------------- #

elif menu == "Analytics":

    render_analytics()


# ---------------- TEST DATA PAGE ---------------- #

elif menu == "Test Data":

    st.markdown("# 🧪 Test Data Generator")
    st.write("Generate mock logs for testing and demonstrations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔥 Quick Actions")
        
        if st.button("🔥 Error Burst (100 logs, 80% errors)", use_container_width=True):
            with st.spinner("Generating error burst..."):
                result = generate_error_burst()
                if result:
                    st.success(f"✅ {result.get('message', 'Logs generated!')}")
                    st.info("👉 Check 'Active Incidents' page to see incidents created")
                    st.rerun()
                else:
                    st.error("Failed to generate error burst")
    
    with col2:
        st.markdown("### 📊 Normal Traffic")
        
        if st.button("📊 Normal Traffic (50 logs)", use_container_width=True):
            with st.spinner("Generating normal traffic..."):
                result = generate_normal_traffic()
                if result:
                    st.success(f"✅ {result.get('message', 'Logs generated!')}")
                    st.rerun()
                else:
                    st.error("Failed to generate normal traffic")
    
    st.divider()
    
    st.markdown("### 🎲 Custom Batch")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        batch_size = st.number_input("Batch Size", min_value=10, max_value=500, value=100)
    
    with col2:
        error_burst = st.checkbox("Error Burst (80% errors)", value=True)
    
    with col3:
        service_filter = st.selectbox(
            "Service (optional)", 
            ["All", "payment", "auth", "api", "worker", "frontend", "database"]
        )
    
    if st.button("🚀 Generate Custom Batch", use_container_width=True):
        service = None if service_filter == "All" else service_filter
        with st.spinner(f"Generating {batch_size} logs..."):
            result = generate_custom_batch(batch_size=batch_size, error_burst=error_burst, service=service)
            if result:
                st.success(f"✅ {result.get('message', 'Logs generated!')}")
                st.json(result)
                st.rerun()
            else:
                st.error("Failed to generate custom batch")
    
    st.divider()
    
    # Display current stats
    st.markdown("### 📊 Current System State")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Logs", stats.get("total_logs", 0))
    with col2:
        st.metric("Error Logs", stats.get("error_count", 0))
    with col3:
        st.metric("Active Incidents", len(incidents))


# ---------------- SETTINGS ---------------- #

elif menu == "Settings":

    st.markdown("<h1>System Settings</h1>", unsafe_allow_html=True)
    st.write("Configuration and integrations.")

    with st.expander("API Configuration"):
        st.write(f"Backend URL: `{API_URL}`")
        st.write("Status: 🟢 Connected" if stats else "Status: 🔴 Disconnected")

    with st.expander("UI Configuration"):
        st.write(f"Theme: `{THEME}`")
        st.write(f"Primary Color: `{PRIMARY_COLOR}`")
        st.write(f"Auto-refresh: `{ENABLE_AUTO_REFRESH}` ({AUTO_REFRESH_INTERVAL}ms)")

    with st.expander("AI Integration"):
        st.write("Model: `Gemini 2.5 Flash`")
        st.write("Purpose: Automated Triage & Recommendation")
    
    with st.expander("🔄 Log Generator (Quick Access)"):
        st.write("Generate test logs directly from settings")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔥 Error Burst", use_container_width=True):
                with st.spinner("Generating..."):
                    result = generate_error_burst()
                    if result:
                        st.success("✅ Logs generated!")
                        st.rerun()
        with col2:
            if st.button("📊 Normal Traffic", use_container_width=True):
                with st.spinner("Generating..."):
                    result = generate_normal_traffic()
                    if result:
                        st.success("✅ Logs generated!")
                        st.rerun()