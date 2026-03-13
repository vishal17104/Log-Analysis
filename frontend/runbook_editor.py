import streamlit as st
import requests

API_URL = "http://localhost:8000"


def render_runbook_editor():

    st.title("📚 Runbook Manager")

    edit = st.session_state.get("edit_runbook")

    # ---------------- EDITOR ----------------

    if edit:
        st.subheader("✏️ Edit Runbook")
    else:
        st.subheader("➕ Create Runbook")

    service = st.text_input(
        "Service",
        value=edit["service"] if edit else "",
        disabled=bool(edit)
    )

    error_type = st.text_input(
        "Error Type",
        value=edit["error_type"] if edit else "",
        disabled=bool(edit)
    )

    title = st.text_input(
        "Title",
        value=edit.get("title", "") if edit else ""
    )

    content = st.text_area(
        "Content",
        value=edit["content"] if edit else "",
        height=200
    )

    tags = st.text_input(
        "Tags (comma separated)",
        value=",".join(edit.get("tags", [])) if edit else ""
    )

    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    col1, col2 = st.columns(2)

    # ---------------- UPDATE ----------------

    if edit:

        with col1:
            if st.button("Update Runbook"):

                payload = {
                    "title": title,
                    "content": content,
                    "tags": tag_list
                }

                res = requests.put(
                    f"{API_URL}/runbooks/{service}/{error_type}",
                    json=payload
                )

                if res.status_code == 200:
                    st.success("Runbook updated")
                    st.session_state.pop("edit_runbook", None)
                    st.rerun()
                else:
                    st.error(res.text)

        with col2:
            if st.button("Cancel Edit"):
                st.session_state.pop("edit_runbook", None)
                st.rerun()

    # ---------------- CREATE ----------------

    else:

        if st.button("Create Runbook"):

            payload = {
                "service": service,
                "error_type": error_type,
                "title": title,
                "content": content,
                "tags": tag_list
            }

            res = requests.post(
                f"{API_URL}/runbooks",
                json=payload
            )

            if res.status_code in [200, 201]:
                st.success("Runbook created!")
                st.rerun()
            else:
                st.error(res.text)

    st.divider()

    # ---------------- RUNBOOK LIST ----------------

    st.subheader("Existing Runbooks")

    try:

        res = requests.get(f"{API_URL}/runbooks/")

        if res.status_code == 200:

            runbooks = res.json()

            if not runbooks:
                st.info("No runbooks found")

            for rb in runbooks:

                service = rb.get("service")
                error_type = rb.get("error_type")
                title = rb.get("title", "Untitled")
                content = rb.get("content", "")
                tags = rb.get("tags", [])
                runbook_id = rb.get("id")

                with st.expander(f"{service} - {title}"):

                    st.code(content)

                    if tags:
                        st.write("Tags:", ", ".join(tags))

                    col1, col2 = st.columns(2)

                    # EDIT
                    with col1:
                        if st.button("Edit", key=f"edit_{runbook_id}"):
                            st.session_state["edit_runbook"] = rb
                            st.rerun()

                    # DELETE
                    with col2:
                        if st.button("Delete", key=f"delete_{runbook_id}"):

                            response = requests.delete(
                                f"{API_URL}/runbooks/{service}/{error_type}"
                            )

                            if response.status_code in [200, 204]:
                                st.success("Runbook deleted")
                                st.rerun()
                            else:
                                st.error(response.text)

        else:
            st.error("Failed to fetch runbooks")

    except Exception as e:
        st.error(f"Connection error: {e}")