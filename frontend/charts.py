import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def render_error_frequency(stats):
    st.write("### Error Frequency (24h)")
    
    if not stats or "timeline" not in stats or not stats["timeline"]:
        st.info("No timeline data available.")
        return

    df = pd.DataFrame(stats["timeline"])
    df['minute'] = pd.to_datetime(df['minute'])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['minute'],
        y=df['count'],
        fill='tozeroy',
        mode='lines',
        line=dict(width=3, color='#00d1ff'),
        fillcolor='rgba(0, 209, 255, 0.1)'
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="#808495")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1e2130",
            tickfont=dict(color="#808495")
        ),
        height=300,
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)


def render_severity_distribution(incidents):

    st.write("### Incident Severity Distribution")

    if not incidents:
        st.info("No incident data.")
        return

    df = pd.DataFrame(incidents)

    sev_order = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

    colors = {
        'LOW': '#00d1ff',
        'MEDIUM': '#ffd700',
        'HIGH': '#ff8c00',
        'CRITICAL': '#ff4b4b'
    }

    counts = df['severity'].value_counts().reindex(sev_order).fillna(0).reset_index()
    counts.columns = ['Severity', 'Count']

    fig = px.bar(
        counts,
        x='Severity',
        y='Count',
        color='Severity',
        color_discrete_map=colors,
        template="plotly_dark"
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)


# ---------- NEW DAY 21 CHART ----------
def render_incidents_by_service(incidents):

    st.write("### Incidents by Service")

    if not incidents:
        st.info("No incident data.")
        return

    df = pd.DataFrame(incidents)

    service_counts = df["service"].value_counts().reset_index()
    service_counts.columns = ["Service", "Count"]

    fig = px.bar(
        service_counts,
        x="Service",
        y="Count",
        color="Service",
        template="plotly_dark"
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)