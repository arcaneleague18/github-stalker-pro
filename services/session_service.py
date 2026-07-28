import streamlit as st
from typing import Optional, Any
from models import ChatMessage, ToolCallLog
from utils import get_logger

logger = get_logger(__name__)

class SessionService:
    """Type-safe manager for Streamlit session state."""

    def init_session(self):
        """Initialize default session state keys if not already present."""
        if "initialized" not in st.session_state:
            st.session_state.initialized = True
            st.session_state.current_username = None
            st.session_state.selected_repository = None
            st.session_state.messages = []
            st.session_state.mcp_status = "Disconnected"
            st.session_state.mcp_logs = []
            logger.info("Initialized new Streamlit session state")

    @property
    def current_username(self) -> Optional[str]:
        return st.session_state.get("current_username")

    def set_username(self, username: Optional[str]):
        """Set the active GitHub username and reset repository focus."""
        if username != self.current_username:
            st.session_state.current_username = username.strip() if username else None
            st.session_state.selected_repository = None
            logger.info(f"Session active user changed to: {st.session_state.current_username}")

    @property
    def selected_repository(self) -> Optional[str]:
        return st.session_state.get("selected_repository")

    def set_repository(self, repo_name: Optional[str]):
        """Set the active repository focus for chat context."""
        st.session_state.selected_repository = repo_name
        logger.info(f"Session active repository changed to: {repo_name}")

    @property
    def messages(self) -> list[ChatMessage]:
        return st.session_state.get("messages", [])

    def add_message(self, role: str, content: str, tool_calls: Optional[list[ToolCallLog]] = None):
        """Append a new message to the conversation history."""
        from datetime import datetime
        msg = ChatMessage(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            timestamp=datetime.now().strftime("%H:%M:%S")
        )
        if "messages" not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append(msg)
        logger.debug(f"Added {role} message to session history (total: {len(st.session_state.messages)})")

    def clear_chat(self):
        """Clear conversation history while maintaining the selected GitHub user."""
        st.session_state.messages = []
        st.session_state.mcp_logs = []
        logger.info("Cleared conversation history")

    @property
    def mcp_status(self) -> str:
        return st.session_state.get("mcp_status", "Disconnected")

    def set_mcp_status(self, status: str):
        st.session_state.mcp_status = status

    @property
    def mcp_logs(self) -> list[str]:
        return st.session_state.get("mcp_logs", [])

    def add_mcp_log(self, log_msg: str):
        if "mcp_logs" not in st.session_state:
            st.session_state.mcp_logs = []
        st.session_state.mcp_logs.append(log_msg)

# Global session service instance
session_service = SessionService()
