import pandas as pd
import streamlit as st


def severity_chart(incidents):

    if not incidents:
        st.warning("No incidents found to chart.")
        return

    df = pd.DataFrame(incidents)

    st.subheader("🔥 Incidents by Severity")

    st.bar_chart(df["severity"].value_counts())


def service_chart(incidents):

    if not incidents:
        return

    df = pd.DataFrame(incidents)

    # Extract service name from title
    df["service"] = df["title"].str.extract(
        r"in\s+(\w+)\s+service", expand=False
    )

    st.subheader("🏢 Affected Services")

    st.bar_chart(df["service"].value_counts())