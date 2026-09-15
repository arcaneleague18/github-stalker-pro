import streamlit as st
from pathlib import Path
from config import settings
from services import session_service, mcp_client
from ui import render_sidebar, render_dashboard, render_chat_interface, render_comparison_page
from utils import get_logger

logger = get_logger(__name__)

def load_css():
    """Load custom dark theme glassmorphism stylesheet."""
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        logger.warning(f"CSS file not found at {css_path}")

def render_welcome_screen():
    """Render welcome hero screen when no GitHub target account is selected."""
    st.markdown(
        """
        <div style="text-align:center; padding:2rem 1rem 1rem 1rem; max-width:850px; margin:0 auto;">
            <h1 style="font-size:3rem; font-weight:700; background:linear-gradient(135deg, #58a6ff 0%, #a371f7 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0.8rem;">
                GitHub Stalker Pro
            </h1>
            <p style="font-size:1.15rem; color:#8b949e; line-height:1.6; margin-bottom:1.8rem;">
                A production-grade AI engineering platform powered by the <b>Model Context Protocol (MCP)</b>.<br/>
                Dynamically explore, analyze, and chat with any public GitHub account without RAG pipelines or vector databases.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Centered Hero Search Bar
    search_container = st.container()
    with search_container:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            with st.form(key="welcome_hero_form", clear_on_submit=False):
                c_in, c_btn = st.columns([3, 1], gap="small")
                with c_in:
                    hero_username = st.text_input(
                        label="GitHub Username",
                        label_visibility="collapsed",
                        placeholder="Enter GitHub username...",
                        key="hero_username_input"
                    )
                with c_btn:
                    hero_submit = st.form_submit_button("🚀 Analyze", use_container_width=True, type="primary")

                if hero_submit:
                    if hero_username and hero_username.strip():
                        session_service.set_username(hero_username.strip())
                        st.toast(f"Target locked: @{hero_username.strip()}")
                        st.rerun()
                    else:
                        st.warning("Please enter a valid GitHub username.")

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="glass-card" style="text-align:center; height:100%;">
                <div style="font-size:2.5rem; margin-bottom:0.8rem;">⚙️</div>
                <h3 style="color:#e6edf3; font-size:1.2rem; margin-bottom:0.5rem;">Dynamic MCP Tooling</h3>
                <p style="color:#8b949e; font-size:0.9rem; line-height:1.5;">
                    The OpenAI LLM autonomously calls GitHub MCP tools in real-time to inspect repository trees, read files, and check commits.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
            <div class="glass-card" style="text-align:center; height:100%;">
                <div style="font-size:2.5rem; margin-bottom:0.8rem;">📊</div>
                <h3 style="color:#e6edf3; font-size:1.2rem; margin-bottom:0.5rem;">Rich Visual Dashboard</h3>
                <p style="color:#8b949e; font-size:0.9rem; line-height:1.5;">
                    Comprehensive profile cards, star/fork metrics, language distribution charts, and organization memberships at a glance.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            """
            <div class="glass-card" style="text-align:center; height:100%;">
                <div style="font-size:2.5rem; margin-bottom:0.8rem;">💬</div>
                <h3 style="color:#e6edf3; font-size:1.2rem; margin-bottom:0.5rem;">Deep AI Architecture Chat</h3>
                <p style="color:#8b949e; font-size:0.9rem; line-height:1.5;">
                    Ask architectural questions, locate specific tech stacks (Docker, FastAPI, React), and summarize developer contributions.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.info("💡 **Tip:** You can enter any public GitHub username above or use the sidebar anytime to switch accounts or inspect metrics.")

def single_inspector_page():
    """Page 1: Single account dashboard and AI chat interface."""
    render_sidebar(is_comparison=False)

    valid, errors = settings.validate_config()
    if not valid:
        for err in errors:
            st.warning(f"⚠️ **Configuration Notice:** {err}")

    current_user = session_service.current_username
    if current_user:
        tab_dash, tab_chat = st.tabs(["📊 Account Dashboard", "💬 AI Assistant Chat"])
        with tab_dash:
            render_dashboard(current_user)
        with tab_chat:
            render_chat_interface()
    else:
        render_welcome_screen()

def compare_page():
    """Page 2: Developer head-to-head comparison showdown."""
    render_sidebar(is_comparison=True)
    render_comparison_page()

def main():
    """Main application loop with multi-page navigation."""
    st.set_page_config(
        page_title=settings.app_title,
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    load_css()
    session_service.init_session()
    mcp_client.connect()

    page_inspector = st.Page(
        single_inspector_page,
        title="Account Inspector",
        icon="👤",
        default=True,
        url_path="inspector"
    )
    page_compare = st.Page(
        compare_page,
        title="Compare Developers",
        icon="⚔️",
        url_path="compare"
    )

    nav = st.navigation(
        [page_inspector, page_compare],
        position="sidebar"
    )
    nav.run()

if __name__ == "__main__":
    main()
