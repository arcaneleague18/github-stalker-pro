import json
import streamlit as st
from services import chat_service, session_service
from utils import get_logger

logger = get_logger(__name__)

# Complete list of suggested questions required by specification
SUGGESTED_QUESTIONS = [
    "Summarize this developer",
    "What are their best repositories?",
    "What technologies do they use?",
    "What programming languages do they use most?",
    "Explain the architecture of their largest project.",
    "What projects use React?",
    "What projects use FastAPI?",
    "Which repositories contain Docker?",
    "Which repositories use PostgreSQL?",
    "Explain the authentication implementation.",
    "Show recent activity.",
    "What open-source projects do they maintain?"
]

def render_chat_interface():
    """Render ChatGPT-style conversation interface with streaming and MCP execution logs."""
    username = session_service.current_username
    selected_repo = session_service.selected_repository

    # Banner showing active conversation context
    ctx_badge = f"@{username}"
    if selected_repo:
        ctx_badge += f" /  {selected_repo}"

    st.markdown(
        f"""
        <div style="background:#161b22; padding:0.8rem 1.2rem; border-radius:12px; border:1px solid #30363d; margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="color:#8b949e; font-size:0.85rem;">Active AI Context: </span>
                <strong style="color:#58a6ff; font-size:1rem;">{ctx_badge}</strong>
            </div>
            <div style="font-size:0.8rem; color:#a371f7; font-family:'JetBrains Mono',monospace;">
                 MCP Tool Calling Enabled
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # 1. Suggested Questions Grid
    # ==========================================
    with st.expander(" Suggested AI Prompts (Click to ask)", expanded=len(session_service.messages) == 0):
        cols = st.columns(3)
        for idx, q in enumerate(SUGGESTED_QUESTIONS):
            with cols[idx % 3]:
                if st.button(f" {q}", key=f"sug_btn_{idx}", use_container_width=True):
                    # Record prompt in session state to trigger immediately below
                    st.session_state.pending_prompt = q
                    st.rerun()

    # ==========================================
    # 2. Render Existing Conversation History
    # ==========================================
    for msg in session_service.messages:
        # We only display user and assistant messages in the main UI thread
        if msg.role in ["user", "assistant"]:
            
            with st.chat_message(msg.role):
                if msg.content:
                    st.markdown(msg.content, unsafe_allow_html=True)
                elif msg.role == "assistant":
                    st.markdown("*(Inspection completed using GitHub MCP tools — see execution log below)*")
                
                # Render any executed MCP tool logs in an expandable inspection block
                if msg.tool_calls:
                    with st.expander(f"Executed {len(msg.tool_calls)} MCP Tool(s)", expanded=False):
                        for tc in msg.tool_calls:
                            status_label = "[SUCCESS]" if tc.status == "success" else "[ERROR]"
                            st.markdown(f"**{status_label} `{tc.tool_name}`**")
                            st.code(f"Arguments: {json.dumps(tc.arguments, indent=2)}", language="json")
                            if tc.result:
                                res_preview = tc.result[:400] + "..." if len(tc.result) > 400 else tc.result
                                st.code(f"Output:\n{res_preview}", language="text")

    # ==========================================
    # 3. Handle New Input & Streaming Response
    # ==========================================
    # Check if a prompt was triggered from suggested questions or chat input
    user_input = st.chat_input(placeholder=f"Ask a question about @{username}'s code, architecture, or repositories...")
    
    pending = st.session_state.pop("pending_prompt", None)
    active_prompt = user_input or pending

    if active_prompt:
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(active_prompt)
        session_service.add_message("user", active_prompt)

        # Display AI streaming response
        with st.chat_message("assistant"):
            status_container = st.container()
            
            with st.spinner("🤖 Analyzing repository context via Model Context Protocol..."):
                stream_generator = chat_service.stream_chat_response(active_prompt, status_container=status_container)
                
                # Use Streamlit write_stream for live typing effect and syntax highlighting
                full_response = st.write_stream(stream_generator)

            # Retrieve any tools called during this turn
            tool_logs = chat_service.get_last_tool_logs()
            
            # Ensure full_response is never saved as empty string
            if not full_response or not str(full_response).strip():
                if tool_logs:
                    full_response = "*(Completed MCP repository inspection — see tool details below)*"
                else:
                    full_response = "No response was generated. Please try asking again."

            # Save final assistant message to session state
            session_service.add_message("assistant", full_response, tool_calls=tool_logs)

        # Rerun to cleanly update conversation state and auto-scroll
        st.rerun()
