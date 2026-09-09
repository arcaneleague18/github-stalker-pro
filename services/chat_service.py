import json
from typing import Any, Generator, Optional
import streamlit as st
from utils.icons import ICONS
from models import ChatMessage, ToolCallLog
from utils import get_logger
from .mcp_service import mcp_client
from .openai_service import openai_service
from .session_service import session_service

logger = get_logger(__name__)

# Mandatory System Prompt required by specification
BASE_SYSTEM_PROMPT = """You are an AI assistant specialized in GitHub repositories and software engineering.

Always answer by using the GitHub MCP tools whenever additional information is required.

Never invent repositories.

Never invent files.

Never invent code.

If information is unavailable, clearly state that it could not be found.

Reference repository names and file paths whenever possible.

CRITICAL EFFICIENCY RULES:
1. When asked to find issues or pull requests opened by a user globally, DO NOT loop through repositories using `list_issues`. Instead, use the `search_issues` tool with the query `author:USERNAME type:issue` or `author:USERNAME type:pr`.
2. Do not call `list_issues` one-by-one unless specifically asked to analyze issues for a single specific repository.
3. When asked for the "total number of contributions", "commits", "issues", or "PRs" for a specific timeframe, use the `get_user_contributions` tool with the username and `date_query` (e.g. `>2026-06-01` or `2025-01-01..2025-12-31`). This tool automatically counts commits, issues, and PRs all at once and returns the grand total."""

class ChatService:
    """Orchestrates multi-turn chat loops, system prompt injection, and dynamic MCP tool execution."""

    def build_system_prompt(self, username: Optional[str], selected_repo: Optional[str] = None) -> str:
        """Construct the system prompt dynamically injecting the current GitHub user and repo focus."""
        prompt_parts = [BASE_SYSTEM_PROMPT]
        
        if username:
            prompt_parts.append(f"\nCurrent GitHub User:\n{username}")
            prompt_parts.append("\nUnless the user specifies another repository or username, assume every question refers to this GitHub account.")
            
        if selected_repo:
            prompt_parts.append(f"\nCurrent Selected Repository Focus:\n{selected_repo}")
            prompt_parts.append("Prioritize checking this repository when answering questions about project architecture, files, or code.")
            
        return "\n".join(prompt_parts)

    def prepare_messages(self, user_prompt: str) -> list[dict[str, Any]]:
        """Format session conversation history into OpenAI API message list format."""
        username = session_service.current_username
        selected_repo = session_service.selected_repository
        
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.build_system_prompt(username, selected_repo)}
        ]

        # Add existing session messages
        for msg in session_service.messages:
            if msg.role == "assistant" and msg.tool_calls:
                # Reconstruct tool calls format for OpenAI API
                t_calls = []
                tool_result_messages = []
                for tc in msg.tool_calls:
                    t_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.tool_name,
                            "arguments": json.dumps(tc.arguments)
                        }
                    })
                    tool_result_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.tool_name,
                        "content": str(tc.result) if tc.result else "No content returned."
                    })
                messages.append({"role": "assistant", "content": msg.content or None, "tool_calls": t_calls})
                messages.extend(tool_result_messages)
            elif msg.role == "tool":
                # Skip standalone tool messages as they are reconstructed above
                pass
            else:
                messages.append({"role": msg.role, "content": msg.content})

        # Append the new user prompt
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def stream_chat_response(
        self,
        user_prompt: str,
        status_container: Optional[Any] = None,
        max_tool_turns: int = 5
    ) -> Generator[str, None, None]:
        """Stream chat completion from OpenAI, dynamically executing MCP tools when requested.
        
        Args:
            user_prompt: The user's input question.
            status_container: Optional Streamlit container/expander to display live MCP execution status.
            max_tool_turns: Maximum number of iterative tool calling turns to prevent infinite loops.
        """
        # Ensure MCP client is connected
        if not mcp_client.connected:
            mcp_client.connect()

        # Prepare messages
        messages = self.prepare_messages(user_prompt)
        tools = mcp_client.get_openai_tools()

        turn_count = 0
        executed_tool_logs: list[ToolCallLog] = []

        while turn_count < max_tool_turns:
            turn_count += 1
            logger.info(f"Chat streaming turn {turn_count} started")
            
            stream = openai_service.stream_chat_with_tools(messages, tools=tools)
            current_turn_tool_calls: list[ToolCallLog] = []

            for item in stream:
                if isinstance(item, str):
                    yield item
                elif isinstance(item, list):
                    # These are ToolCallLog objects requested by the model
                    current_turn_tool_calls = item

            # If no tool calls were generated, the assistant finished its response!
            if not current_turn_tool_calls:
                break

            # Execute requested MCP tools
            for tc in current_turn_tool_calls:
                logger.info(f"Executing tool '{tc.tool_name}' requested by LLM")
                
                # Update UI status if container provided
                if status_container is not None:
                    with status_container:
                        st.markdown(
                            f"""<div class="tool-status-badge">
                            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNhMzcxZjciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBzdHlsZT0idmVydGljYWwtYWxpZ246IG1pZGRsZTsiPjxwYXRoIGQ9Ik0xNC43IDYuM2ExIDEgMCAwIDAgMCAxLjRsMS42IDEuNmExIDEgMCAwIDAgMS40IDBsMy43Ny0zLjc3YTYgNiAwIDAgMS03Ljk0IDcuOTRsLTYuOTEgNi45MWEyLjEyIDIuMTIgMCAwIDEtMy0zbDYuOTEtNi45MWE2IDYgMCAwIDEgNy45NC03Ljk0bC0zLjc2IDMuNzZ6Ii8+PC9zdmc+"> Calling MCP Tool: <b>{tc.tool_name}</b><br/>
                            <span style="font-size:0.75rem; color:#8b949e;">Args: {json.dumps(tc.arguments)}</span>
                            </div>""",
                            unsafe_allow_html=True
                        )
                        session_service.add_mcp_log(f"Called `{tc.tool_name}` with `{json.dumps(tc.arguments)}`")

                # Execute MCP tool via mcp_client
                try:
                    result_str = mcp_client.call_tool(tc.tool_name, tc.arguments)
                    tc.result = result_str
                    tc.status = "success"
                except Exception as e:
                    tc.result = f"Error executing tool: {str(e)}"
                    tc.status = "error"
                    tc.error_message = str(e)
                    logger.error(f"MCP execution error for '{tc.tool_name}': {e}")

                executed_tool_logs.append(tc)

            # Append assistant tool call request to message history for next turn
            api_tool_calls = []
            for tc in current_turn_tool_calls:
                api_tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.tool_name,
                        "arguments": json.dumps(tc.arguments)
                    }
                })
            messages.append({"role": "assistant", "content": None, "tool_calls": api_tool_calls})

            # Append tool execution outputs to message history for next turn
            for tc in current_turn_tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.tool_name,
                    "content": tc.result or "No content returned."
                })

        # Save completed message with any executed tool logs to session history
        # Note: The calling UI will capture the streamed text to record the assistant's final content.
        self._last_executed_tool_logs = executed_tool_logs

    def get_last_tool_logs(self) -> list[ToolCallLog]:
        return getattr(self, "_last_executed_tool_logs", [])

# Global chat service instance
chat_service = ChatService()
