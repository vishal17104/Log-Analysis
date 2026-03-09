import streamlit as st
from api_client import get_logs


def render_log_feed():

    st.subheader("Live Log Feed")

    if "log_history" not in st.session_state:
        st.session_state.log_history = []

    logs = get_logs(limit=25)

    if logs:
        st.session_state.log_history = logs

    logs_to_show = st.session_state.log_history

    if not logs_to_show:
        st.info("Waiting for logs...")
        return

    for log in logs_to_show:

        text = f"[{log['timestamp']}] {log['service']} - {log['message']}"

        level = log.get("level", "")

        if level == "ERROR":
            st.error(text)

        elif level == "WARNING":
            st.warning(text)

        else:
            st.write(text)