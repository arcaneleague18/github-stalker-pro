import streamlit as st
from pathlib import Path
from config import settings
from services import session_service, mcp_client
from ui import render_sidebar, render_dashboard, render_chat_interface
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
        <div style="text-align:center; padding:3rem 1rem; max-width:850px; margin:0 auto;">
            <h1 style="font-size:3rem; font-weight:700; background:linear-gradient(135deg, #58a6ff 0%, #a371f7 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:1rem;">
                Github Stalker pro
            </h1>
            <p style="font-size:1.25rem; color:#8b949e; line-height:1.6; margin-bottom:2.5rem;">
                A production-grade AI engineering platform powered by the <b>Model Context Protocol (MCP)</b>.
                Dynamically explore, analyze, and chat with any public GitHub account without RAG pipelines, vector databases, or embeddings.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="glass-card" style="text-align:center; height:100%;">
                <div style="font-size:2.5rem; margin-bottom:0.8rem;">&#9881;</div>
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
                <div style="font-size:2.5rem; margin-bottom:0.8rem;">&#9783;</div>
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
                <div style="font-size:2.5rem; margin-bottom:0.8rem;">&#10094;/&#10095;</div>
                <h3 style="color:#e6edf3; font-size:1.2rem; margin-bottom:0.5rem;">Deep AI Architecture Chat</h3>
                <p style="color:#8b949e; font-size:0.9rem; line-height:1.5;">
                    Ask architectural questions, locate specific tech stacks (Docker, FastAPI, React), and summarize developer contributions.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.info(" **Get Started:** Enter a GitHub username in the sidebar on the left and click ** Analyze Account**!")

def main():
    """Main application loop."""
    # 1. Page configuration
    st.set_page_config(
        page_title=settings.app_title,
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. Load custom styles and initialize session state
    load_css()
    session_service.init_session()

    # 3. Connect to MCP Server (silent background check or HTTP adapter)
    mcp_client.connect()

    # 4. Render Sidebar navigation
    render_sidebar()

    # 5. Validate configuration warnings
    valid, errors = settings.validate_config()
    if not valid:
        for err in errors:
            st.warning(f"️ **Configuration Notice:** {err}")

    # 6. Render main workspace views
    current_user = session_service.current_username
    if current_user:
        # Create tabbed navigation for Dashboard and AI Chat
        tab_dash, tab_chat = st.tabs([" Account Dashboard", " AI Assistant Chat"])
        
        with tab_dash:
            render_dashboard(current_user)
            
        with tab_chat:
            render_chat_interface()
    else:
        render_welcome_screen()

if __name__ == "__main__":
    main()
