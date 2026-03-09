import streamlit as st

def render_incident_list(incidents):
    st.write("## Active Incidents")
    st.write("Current ongoing investigations across the fleet")
    st.write("")

    if not incidents:
        st.success("✅ System Clean: No active incidents.")
        return

    for inc in incidents:
        # Match colors to Image 3
        sev = inc['severity'].upper()
        color = "#ff4b4b" if sev == "CRITICAL" else "#ff8c00" if sev == "HIGH" else "#ffd700" if sev == "MEDIUM" else "#00d1ff"
        
        # Incident Card HTML
        st.markdown(f"""
            <div style="
                background-color: #1e2130; 
                padding: 20px; 
                border-radius: 12px; 
                border-left: 6px solid {color}; 
                margin-bottom: 15px;
                border-top: 1px solid #2d313e;
                border-right: 1px solid #2d313e;
                border-bottom: 1px solid #2d313e;
            ">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <span style="color: #808495; font-size: 11px; font-weight: bold; letter-spacing: 1px;">INC-{inc['id']}</span>
                        <span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 10px;">{sev}</span>
                    </div>
                </div>
                <h3 style="margin: 12px 0 6px 0; color: white; font-family: sans-serif;">{inc['title']}</h3>
                <div style="display: flex; gap: 15px;">
                    <span style="color: #00d1ff; font-size: 14px;">{inc.get('service', 'api-gateway')}</span>
                    <span style="color: #808495; font-size: 14px;">• {inc.get('detected_at', '21:59:48')}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)