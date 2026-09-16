import streamlit as st
from services import session_service, mcp_client, github_service, openai_service
from utils import get_logger

logger = get_logger(__name__)

def render_sidebar(is_comparison: bool = False):
    """Render sidebar navigation, user input, and session controls."""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding-bottom:0.4rem; border-bottom:1px solid #30363d; margin-bottom:0.8rem;">
                <h2 style="color:#58a6ff; margin:0; font-size:1.25rem; font-weight:700;">🤖 GitHub Stalker Pro</h2>
                <p style="color:#8b949e; font-size:0.75rem; margin-top:0.1rem; margin-bottom:0;">AI-Powered MCP Analytics</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Connection Status Indicators (Unified Compact Card)
        mcp_color = "#238636" if mcp_client.connected else "#da3633"
        mcp_text = "Connected (MCP)" if mcp_client.connected else "Offline"

        llm_connected, llm_status_text = openai_service.check_connection()
        llm_color = "#238636" if llm_connected else "#da3633"

        st.markdown(
            f"""
            <div style="background:#161b22; padding:0.45rem 0.8rem; border-radius:8px; border:1px solid #30363d; margin-bottom:0.8rem; display:flex; flex-direction:column; gap:0.25rem;">
                <div style="display:flex; align-items:center; justify-content:space-between; font-size:0.8rem;">
                    <span style="color:#c9d1d9;">MCP Server:</span>
                    <span style="color:{mcp_color}; font-weight:600;">● {mcp_text}</span>
                </div>
                <div style="display:flex; align-items:center; justify-content:space-between; font-size:0.8rem; border-top:1px solid #21262d; padding-top:0.25rem;">
                    <span style="color:#c9d1d9;">AI Assistant:</span>
                    <span style="color:{llm_color}; font-weight:600;">● {llm_status_text}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if is_comparison:
            st.markdown(
                """
                <div style="background:rgba(247, 120, 186, 0.1); border:1px solid rgba(247, 120, 186, 0.3); padding:0.8rem; border-radius:10px; margin-bottom:0.8rem; text-align:center;">
                    <span style="font-size:0.75rem; color:#f778ba; font-weight:600; display:block; text-transform:uppercase; letter-spacing:0.5px;">⚔️ Mode Active</span>
                    <strong style="color:#ffffff; font-size:1rem;">Developer Comparison</strong>
                    <p style="color:#8b949e; font-size:0.75rem; margin:0.3rem 0 0 0; line-height:1.3;">
                        Side-by-side metric battle and comparative AI assistant.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.session_state.get("compare_submitted"):
                dev1 = st.session_state.get("compare_user1", "")
                dev2 = st.session_state.get("compare_user2", "")
                if dev1 and dev2:
                    st.markdown(
                        f"""
                        <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:0.5rem; text-align:center; font-size:0.8rem; margin-bottom:0.8rem;">
                            <span style="color:#58a6ff; font-weight:600;">@{dev1}</span>
                            <span style="color:#8b949e; margin:0 0.3rem;">vs</span>
                            <span style="color:#f778ba; font-weight:600;">@{dev2}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🔄 Reset", use_container_width=True, help="Change comparison developer targets"):
                        st.session_state.compare_submitted = False
                        st.session_state.compare_ai_analysis = None
                        st.rerun()
                with c2:
                    if st.button("🗑️ Chat", use_container_width=True, help="Clear comparative chat history"):
                        session_service.clear_compare_chat()
                        st.toast("Comparison chat history cleared!")
                        st.rerun()
            return

        st.markdown("<p style='font-size:0.85rem; text-transform:uppercase; color:#8b949e; letter-spacing:0.5px; font-weight:600; margin-bottom:0.4rem;'>🎯 Account Target</p>", unsafe_allow_html=True)

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
                    label_visibility="collapsed",
                    placeholder="Enter GitHub username...",
                    help="Enter any public GitHub account username to analyze."
                )
                analyze_clicked = st.form_submit_button("🚀 Analyze Account", use_container_width=True)

                if analyze_clicked:
                    if username_input and username_input.strip():
                        session_service.set_username(username_input.strip())
                        st.toast(f"Target locked: @{username_input.strip()}")
                        st.rerun()
                    else:
                        st.warning("Please enter a valid GitHub username.")


