import streamlit as st
from services import session_service, mcp_client, github_service
from utils import get_logger

logger = get_logger(__name__)

def render_sidebar():
    """Render sidebar navigation, user input, and session controls."""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding-bottom:1rem; border-bottom:1px solid #30363d; margin-bottom:1.5rem;">
                <h2 style="color:#58a6ff; margin:0; font-weight:700;">🤖 GitHub Insight</h2>
                <p style="color:#8b949e; font-size:0.85rem; margin-top:0.2rem;">AI-Powered MCP Analytics</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # MCP Status Indicator
        status_color = "#238636" if mcp_client.connected else "#da3633"
        status_text = "Connected (MCP)" if mcp_client.connected else "Offline"
        st.markdown(
            f"""
            <div style="background:#161b22; padding:0.6rem 1rem; border-radius:8px; border:1px solid #30363d; margin-bottom:1.5rem; display:flex; align-items:center; justify-content:space-between;">
                <span style="font-size:0.85rem; color:#c9d1d9;">MCP Server:</span>
                <span style="color:{status_color}; font-weight:600; font-size:0.85rem;">● {status_text}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.subheader(" Account Target")

        current_user = session_service.current_username

        if current_user:
            st.markdown(
                f"""
                <div style="background:rgba(56, 139, 253, 0.1); border:1px solid rgba(56, 139, 253, 0.4); padding:0.8rem; border-radius:10px; margin-bottom:1rem; text-align:center;">
                    <span style="font-size:0.8rem; color:#8b949e; display:block;">Active Account</span>
                    <strong style="color:#58a6ff; font-size:1.2rem;">@{current_user}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(" Change User", use_container_width=True):
                    session_service.set_username(None)
                    st.rerun()
            with col2:
                if st.button("️ Clear Chat", use_container_width=True):
                    session_service.clear_chat()
                    st.toast("Conversation history cleared!")
                    st.rerun()

            if st.button(" Refresh Data", use_container_width=True):
                with st.spinner("Refreshing account metrics..."):
                    github_service.clear_cache(current_user)
                    github_service.get_dashboard_metrics(current_user, force_refresh=True)
                st.toast("Data refreshed successfully!")
                st.rerun()

        else:
            with st.form(key="username_form", clear_on_submit=False):
                username_input = st.text_input(
                    label="GitHub Username",
                    placeholder="e.g. torvalds, octocat, gaearon",
                    help="Enter any public GitHub account username to analyze."
                )
                analyze_clicked = st.form_submit_button(" Analyze Account", use_container_width=True)

                if analyze_clicked:
                    if username_input and username_input.strip():
                        session_service.set_username(username_input.strip())
                        st.toast(f"Target locked: @{username_input.strip()}")
                        st.rerun()
                    else:
                        st.warning("Please enter a valid GitHub username.")

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size:0.75rem; color:#8b949e; line-height:1.4;">
                <b>Model Context Protocol (MCP)</b><br/>
                No RAG • No Vector DBs • Dynamic AI Tool Calling directly from GitHub API.
            </div>
            """,
            unsafe_allow_html=True
        )
