import streamlit as st
import requests

API_URL = "http://localhost:8000"


# ---------------- INCIDENT FETCH ---------------- #

@st.cache_data(ttl=10)
def fetch_incidents():
    try:
        response = requests.get(f"{API_URL}/agent/incidents", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []


# ---------------- AGENT API ---------------- #

def process_incident(incident_id):
    try:
        response = requests.post(
            f"{API_URL}/agent/process-incident/{incident_id}",
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def generate_solution(incident_id):
    try:
        response = requests.post(
            f"{API_URL}/agent/generate-solution/{incident_id}",
            timeout=15
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def match_runbook(incident_id):
    try:
        response = requests.post(
            f"{API_URL}/runbooks/match-for-incident/{incident_id}",
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ---------------- INCIDENT SELECTOR ---------------- #

def render_incident_selector(incidents):

    if not incidents:
        st.warning("No incidents found.")
        return None

    options = {
        inc['id']: f"INC-{inc['id']:03d} - {inc['title'][:40]}"
        for inc in incidents
    }

    selected_id = st.selectbox(
        "Select Incident",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )

    selected = next((i for i in incidents if i['id'] == selected_id), None)

    if selected:
        with st.expander("📋 Incident Details", expanded=True):

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Title:** {selected['title']}")
                st.markdown(f"**Severity:** `{selected['severity']}`")

            with col2:
                st.markdown(f"**Service:** {selected.get('service','unknown')}")
                st.markdown(f"**Errors:** {selected['error_count']}")

    return selected_id


# ---------------- ACTION BUTTONS ---------------- #

def render_agent_actions(selected_id):

    if not selected_id:
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🤖 Process Incident", use_container_width=True):
            with st.spinner("Agent analyzing incident..."):
                st.session_state['agent_result'] = process_incident(selected_id)
                st.session_state['action_taken'] = 'process'

    with col2:
        if st.button("💡 Generate Fix", use_container_width=True):
            with st.spinner("Generating solution..."):
                st.session_state['agent_result'] = generate_solution(selected_id)
                st.session_state['action_taken'] = 'fix'

    with col3:
        if st.button("📋 Match Runbook", use_container_width=True):
            with st.spinner("Searching runbooks..."):
                st.session_state['agent_result'] = match_runbook(selected_id)
                st.session_state['action_taken'] = 'runbook'


# ---------------- RESPONSE RENDER ---------------- #

def render_agent_response():

    if 'agent_result' not in st.session_state:
        st.info("👆 Select an incident and run an agent action.")
        return

    result = st.session_state['agent_result']

    if 'error' in result:
        st.error(result['error'])
        return

    st.markdown("### 🤖 Agent Response")

    st.json(result)


# ---------------- MAIN PAGE ---------------- #

def render_agent_control():

    st.markdown("# 🤖 Agent Control")
    st.write("Interact with the AI agent to analyze incidents.")

    try:
        status = requests.get(f"{API_URL}/agent/status", timeout=2).json()
        running = status.get("running", False)

        if running:
            st.caption("🟢 Agent runtime: Active")
        else:
            st.caption("🔴 Agent runtime: Inactive")

    except:
        st.caption("⚫ Agent runtime: Unknown")

    st.divider()

    incidents = fetch_incidents()

    if not incidents:
        st.warning("No incidents available.")
        return

    col1, col2 = st.columns([1,1])

    with col1:
        st.markdown("### 🎯 Select Incident")
        selected_id = render_incident_selector(incidents)

    with col2:
        st.markdown("### ⚡ Agent Actions")
        render_agent_actions(selected_id)

    st.divider()

    render_agent_response()