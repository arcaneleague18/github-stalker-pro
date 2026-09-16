import json
import streamlit as st
from services import chat_service, session_service
from utils import get_logger

logger = get_logger(__name__)

# Curated suggested comparative questions (no hardcoded sample usernames)
COMPARATIVE_SUGGESTED_QUESTIONS = [
    "Did they do any projects together? and what are they?",
    "Are they part of any shared organization?",
    "What are their contributions in that organization?",
    "Do any of their repos have similar kind of architecture?",
    "Compare their primary technology stacks and languages",
    "Who has higher community reach and open-source impact?",
    "How do their code styles and repository structures differ?",
    "Compare the complexity of their top repositories",
    "Which developer has more recent commit and PR activity?"
]

def render_comparison_chat(dev1: str, dev2: str):
    """Render interactive ChatGPT-style cross-developer comparison interface."""
    
    # Active Comparative Context Banner
    st.markdown(
        f"""
        <div style="background:#161b22; padding:0.8rem 1.2rem; border-radius:12px; border:1px solid #30363d; margin-bottom:1.2rem; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="color:#8b949e; font-size:0.85rem;">Active Comparative Context: </span>
                <strong style="color:#58a6ff; font-size:1rem;">@{dev1}</strong>
                <span style="color:#8b949e; margin:0 0.4rem; font-weight:600;">VS</span>
                <strong style="color:#f778ba; font-size:1rem;">@{dev2}</strong>
            </div>
            <div style="font-size:0.8rem; color:#a371f7; font-family:'JetBrains Mono',monospace;">
                ⚡ MCP Cross-Developer Analysis
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # 1. Suggested Comparative Questions Grid
    # ==========================================
    is_empty_history = len(session_service.compare_messages) == 0
    with st.expander("💡 Suggested Comparative Inquiries (Click to ask)", expanded=is_empty_history):
        cols = st.columns(3)
        for idx, q in enumerate(COMPARATIVE_SUGGESTED_QUESTIONS):
            with cols[idx % 3]:
                if st.button(f"🔍 {q}", key=f"comp_sug_btn_{idx}", use_container_width=True):
                    st.session_state.pending_compare_prompt = q
                    st.rerun()

    # ==========================================
    # 2. Render Existing Comparison Conversation History
    # ==========================================
    for msg in session_service.compare_messages:
        if msg.role in ["user", "assistant"]:
            with st.chat_message(msg.role):
                if msg.content:
                    st.markdown(msg.content, unsafe_allow_html=True)

                # Render any executed MCP tool logs in an expandable block
                if msg.tool_calls:
                    with st.expander(f"🛠️ Executed {len(msg.tool_calls)} MCP Tool(s)", expanded=False):
                        for tc in msg.tool_calls:
                            status_icon = "✅" if tc.status == "success" else "❌"
                            st.markdown(f"**{status_icon} `{tc.tool_name}`**")
                            st.code(f"Arguments: {json.dumps(tc.arguments, indent=2)}", language="json")
                            if tc.result:
                                res_preview = tc.result[:400] + "..." if len(tc.result) > 400 else tc.result
                                st.code(f"Output:\n{res_preview}", language="text")

    # ==========================================
    # 3. Handle Input & Streaming Response
    # ==========================================
    user_input = st.chat_input(placeholder=f"Ask about @{dev1} vs @{dev2}'s shared projects, architecture, or organizations...")
    pending = st.session_state.pop("pending_compare_prompt", None)
    active_prompt = user_input or pending

    if active_prompt:
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(active_prompt)
        session_service.add_compare_message("user", active_prompt)

        # Stream AI response using MCP tools in comparison mode
        with st.chat_message("assistant"):
            status_container = st.container()

            with st.spinner(f"🤖 Cross-analyzing @{dev1} and @{dev2} via Model Context Protocol..."):
                stream_gen = chat_service.stream_chat_response(
                    active_prompt,
                    status_container=status_container,
                    is_comparison=True,
                    compare_users=(dev1, dev2)
                )
                full_response = st.write_stream(stream_gen)

            tool_logs = chat_service.get_last_tool_logs()
            session_service.add_compare_message("assistant", full_response, tool_calls=tool_logs)

        st.rerun()
