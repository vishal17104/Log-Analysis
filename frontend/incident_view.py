import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


#Filters & Sorting
def render_incident_filters():
    """filter controls for incidents"""

    st.markdown("### Filter Incidents")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "open", "investigating", "resolved", "closed"]
        )

    with col2:
        severity_filter = st.selectbox(
            "Severity",
            ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
        )

    with col3:
        date_range = st.selectbox(
            "Time Rnage",
            ["Last 24h", "Last 7 days", "Last 30 days", "All time"]
        )

        #convert to days
        days_map = {
            "Last 24h": 1,
            "Last 7 days": 7,
            "Last 30 days": 30,
            "All time": 365
        }
        days = days_map[date_range]

    with col4:
        search = st.text_input("Search", placeholder="ID or title...")

    return status_filter, severity_filter, days, search

def filter_incidents(incidents, status_filter, severity_filter, days, search):
    """Apply filters to incidents"""

    if not incidents:
        return []

    df = pd.DataFrame(incidents)

    #Date filter
    if days < 365:
        cutoff = datetime.now() - timedelta(days=days)
        df['detected_at'] = pd.to_datetime(df['detected_at'])
        df = df[df['detected_at'] >= cutoff]

    #Status filter
    if status_filter != "All":
        df = df[df['status'] == status_filter]

    #Severity filter
    if severity_filter != "All":
        df = df[df['severity'] == severity_filter]

    #Search filter
    if search:
        df = df[
            df['title'].str.contains(search, case = False, na = False) |
            df['id'].astype(str).str.contains(search, na=False)
        ]

    return df.to_dict('records')


def render_sortable_Table(incidents):
    """Sortable table view"""

    if not incidents:
        st.info("No incident data.")
        return

    df = pd.DataFrame(incidents)

    #Add sorting controls

    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            ["detected_at", "severity", "id", "service", "status"]
        )
    with col2:
        sort_order = st.radio(
            "Order",
            ["Ascending", "Descending"],
            horizontal = True
        )

    #Apply sorting
    ascending = (sort_order == "Ascending")
    df = df.sort_values(by=sort_by, ascending=ascending)

    #Display count
    st.caption(f"Showing {len(df)} incidents")

    #Interactive dataframe
    st.dataframe(
        df[['id', 'severity', 'title', 'service', 'status', 'detected_at', 'error_count']],
        use_container_width=True,
        height = 400,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "severity": st.column_config.TextColumn("Severity", width="small"),
            "title": "Title",
            "service": "Service",
            "status": "Status",
            "detected_at": st.column_config.DatetimeColumn("Detected", format="MMM DD, HH:mm"),
            "error_count": st.column_config.NumberColumn("Errors", width="small")
        }
    )

    return df



def render_incident_list(incidents):
    st.write("## Active Incidents")
    st.write("Current ongoing investigations across the fleet")
    st.write("")

    if not incidents:
        st.success("System Clean: No active incidents.")
        return
    
    #filters
    status_filter, severity_filter, days, search = render_incident_filters()

    #Apply filters
    filtered_incidents = filter_incidents(
        incidents, status_filter, severity_filter, days, search
    )

    if not filtered_incidents:
        st.info("No incidents match the selected filters")
        return
    
    df = pd.DataFrame(filtered_incidents)

    #Incident metrics
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

    #Charts

    col1, col2 = st.columns(2)

    #Severity Distribution
    with col1:
        sev_counts = df["severity"].str.upper().value_counts().reset_index()
        sev_counts.columns = ["Severity", "Count"]

        fig = px.bar(
            sev_counts,
            x="Severity",
            y="Count",
            title = "Severity Distribution",
            color="Severity",
        )

        st.plotly_chart(fig, use_container_width=True)

    #Incidents by service
    with col2:
        service_counts = df["service"].value_counts().reset_index()
        service_counts.columns = ["Service", "Count"]

        fig = px.bar(
            service_counts,
            x="Service",
            y="Count",
            title = "Incidents by Service",
            color="Service",
        )

        st.plotly_chart(fig, use_container_width=True)

    st.write("")
    st.write("### Incident Details")

    #View toggle
    view_type = st.radio(
        "View as",
        ["Cards", "Table"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if view_type == "Table":
        render_sortable_Table(filtered_incidents)
    else:
        for inc in filtered_incidents:
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