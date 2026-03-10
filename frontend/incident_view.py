import streamlit as st
import pandas as pd
import plotly.express as px


def render_incident_list(incidents):

    st.write("## Active Incidents")
    st.write("Current ongoing investigations across the fleet")
    st.write("")

    if not incidents:
        st.success("✅ System Clean: No active incidents.")
        return

    df = pd.DataFrame(incidents)

    # ---------- INCIDENT METRICS ----------
    total = len(df)
    critical = len(df[df["severity"].str.upper() == "CRITICAL"])
    high = len(df[df["severity"].str.upper() == "HIGH"])
    medium = len(df[df["severity"].str.upper() == "MEDIUM"])
    low = len(df[df["severity"].str.upper() == "LOW"])

    m1, m2, m3, m4, m5 = st.columns(5)

    m1.metric("Total Incidents", total)
    m2.metric("Critical", critical)
    m3.metric("High", high)
    m4.metric("Medium", medium)
    m5.metric("Low", low)

    st.write("")

    # ---------- CHARTS ----------
    col1, col2 = st.columns(2)

    # Severity Distribution
    with col1:
        sev_counts = df["severity"].str.upper().value_counts().reset_index()
        sev_counts.columns = ["Severity", "Count"]

        fig = px.bar(
            sev_counts,
            x="Severity",
            y="Count",
            title="Severity Distribution",
            color="Severity",
        )

        st.plotly_chart(fig, use_container_width=True)

    # Incidents by Service
    with col2:
        service_counts = df["service"].value_counts().reset_index()
        service_counts.columns = ["Service", "Count"]

        fig2 = px.bar(
            service_counts,
            x="Service",
            y="Count",
            title="Incidents by Service",
            color="Service",
        )

        st.plotly_chart(fig2, use_container_width=True)

    st.write("")
    st.write("### Incident Details")

    # ---------- INCIDENT CARDS ----------
    for inc in incidents:

        sev = inc["severity"].upper()

        color = (
            "#ff4b4b" if sev == "CRITICAL"
            else "#ff8c00" if sev == "HIGH"
            else "#ffd700" if sev == "MEDIUM"
            else "#00d1ff"
        )

        card_html = f"""<div style="background-color:#1e2130;padding:20px;border-radius:12px;border-left:6px solid {color};margin-bottom:15px;border:1px solid #2d313e;">

<div style="display:flex;justify-content:space-between;align-items:center;">
<div>
<span style="color:#808495;font-size:11px;font-weight:bold;">INC-{inc['id']}</span>
<span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:bold;margin-left:10px;">{sev}</span>
</div>
</div>

<h3 style="margin:12px 0 6px 0;color:white;">{inc['title']}</h3>

<div style="display:flex;gap:15px;">
<span style="color:#00d1ff;font-size:14px;">{inc.get('service','api-gateway')}</span>
<span style="color:#808495;font-size:14px;">• {inc.get('detected_at','')}</span>
</div>

</div>"""

        st.markdown(card_html, unsafe_allow_html=True)