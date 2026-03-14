import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import os

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")


def fetch_stats():
    try:
        res = requests.get(f"{API_URL}/logs/stats?minutes=1440")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Error fetching analytics: {e}")

    return None


def render_error_chart(stats):

    st.subheader("📈 Error Frequency (Timeline)")

    if stats and stats.get("timeline"):

        df = pd.DataFrame(stats["timeline"])
        df["minute"] = pd.to_datetime(df["minute"])

        fig = px.line(
            df,
            x="minute",
            y="count",
            title="Errors Detected Per Minute",
            template="plotly_dark",
            color_discrete_sequence=["#00d1ff"]
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No error timeline data available.")


def render_top_services(stats):

    st.subheader("🏢 Top Error Sources")

    if stats and stats.get("by_service"):

        data = stats["by_service"]

        df = pd.DataFrame(
            list(data.items()),
            columns=["Service", "Error Count"]
        )

        fig = px.bar(
            df,
            x="Service",
            y="Error Count",
            color="Service",
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)


def render_incident_trend():

    st.subheader("🚨 Incident History")

    try:

        res = requests.get(f"{API_URL}/incidents?limit=50")

        if res.status_code == 200:

            incidents = res.json()

            if incidents:

                df = pd.DataFrame(incidents)

                df["date"] = pd.to_datetime(
                    df["detected_at"]
                ).dt.date

                trend = (
                    df.groupby("date")
                    .size()
                    .reset_index(name="count")
                )

                fig = px.area(
                    trend,
                    x="date",
                    y="count",
                    title="Incidents Per Day",
                    template="plotly_dark"
                )

                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("No incidents recorded.")

    except Exception:
        st.warning("Could not load incident trends.")


def render_analytics():

    st.title("📊 Sentinel Analytics")
    st.write("Long-term reliability metrics and trend analysis.")

    stats = fetch_stats()

    render_error_chart(stats)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        render_top_services(stats)

    with col2:
        render_incident_trend()