import streamlit as st
import requests

API_URL = "http://localhost:8000"


def render_agent_control():

    st.markdown("<h1>Agent Control</h1>", unsafe_allow_html=True)
    st.write("Manage AI monitoring agents.")

    try:
        status = requests.get(f"{API_URL}/agent/status").json()
        running = status.get("running", False)
    except:
        running = False

    if running:
        st.success("Agent is running")
    else:
        st.warning("Agent is stopped")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Agent"):
            try:
                r = requests.post(f"{API_URL}/agent/start")
                if r.status_code == 200:
                    st.success("Agent started successfully")
                else:
                    st.error("Failed to start agent")
            except:
                st.error("Backend not reachable")
            st.rerun()

    with col2:
        if st.button("Stop Agent"):
            try:
                r = requests.post(f"{API_URL}/agent/stop")
                if r.status_code == 200:
                    st.warning("Agent stopped")
                else:
                    st.error("Failed to stop agent")
            except:
                st.error("Backend not reachable")
            st.rerun()