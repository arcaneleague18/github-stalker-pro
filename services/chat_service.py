import json
from typing import Any, Generator, Optional
import streamlit as st
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

# Comparative System Prompt for cross-developer inquiries
COMPARISON_BASE_SYSTEM_PROMPT = """You are an elite software engineering architect and GitHub intelligence assistant specializing in cross-developer comparative analysis.

You have direct access to GitHub via Model Context Protocol (MCP) tools.

Always answer questions by using the GitHub MCP tools whenever factual information or verification is required.

Never invent repositories. Never invent organizations. Never invent files. Never invent code.

If information is unavailable or no shared history exists, clearly state that fact.

GUIDELINES FOR COMPARATIVE INQUIRIES:
1. Shared Projects & Collaborations ("Did they do any projects together?", "What are they?"):
   - Check if either developer contributed to the other's repositories using `get_repository`, `list_commits`, or `search_issues` with queries like `author:USER1 repo:USER2/REPO` or `mentions:USER1 repo:USER2/REPO`.
   - Use `search_issues` (e.g. `type:pr author:USER1 repo:USER2/...`) or `search_repositories` to find mutual repositories where both have participated.
2. Shared Organizations & Contributions ("Are they part of any organization?", "What are their contributions in that organization?"):
   - Call `list_user_organizations` for both developers to retrieve their public memberships and discover overlapping organizations.
   - For shared organizations, use `search_issues` (e.g. `org:ORG_NAME author:USER1` and `org:ORG_NAME author:USER2`) to contrast their respective issue/PR contributions.
3. Architecture, Code Quality & Tech Stack Comparison ("Do any of their repos have similar architecture?"):
   - Call `list_user_repositories` for both developers to view their project catalog and star/fork distributions.
   - Use `get_repository_tree` and `get_file_contents` to inspect file trees, configuration manifests (e.g., package.json, Cargo.toml, pyproject.toml, Dockerfile), and READMEs of their flagship repositories to compare design patterns, modular architecture, and tech stacks.
4. Tone & Style:
   - Provide articulate, structured, and insightful comparisons highlighting complementary engineering strengths, differing architectural paradigms, and open-source reach."""

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

    def build_comparison_system_prompt(self, user1: str, user2: str) -> str:
        """Construct the system prompt specifically for dual-developer comparisons."""
        return (
            f"{COMPARISON_BASE_SYSTEM_PROMPT}\n\n"
            f"Active Comparison Targets:\n"
            f"- Developer 1: @{user1}\n"
            f"- Developer 2: @{user2}\n\n"
            f"Always consider both developers (@{user1} and @{user2}) when interpreting and answering questions."
        )

    def prepare_messages(
        self,
        user_prompt: str,
        is_comparison: bool = False,
        compare_users: Optional[tuple[str, str]] = None
    ) -> list[dict[str, Any]]:
        """Format session conversation history into OpenAI API message list format."""
        if is_comparison and compare_users:
            u1, u2 = compare_users
            sys_prompt = self.build_comparison_system_prompt(u1, u2)
            source_messages = session_service.compare_messages
        else:
            username = session_service.current_username
            selected_repo = session_service.selected_repository
            sys_prompt = self.build_system_prompt(username, selected_repo)
            source_messages = session_service.messages

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": sys_prompt}
        ]

        # Add existing session messages
        for msg in source_messages:
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
        max_tool_turns: int = 5,
        is_comparison: bool = False,
        compare_users: Optional[tuple[str, str]] = None
    ) -> Generator[str, None, None]:
        """Stream chat completion from OpenAI, dynamically executing MCP tools when requested.
        
        Args:
            user_prompt: The user's input question.
            status_container: Optional Streamlit container/expander to display live MCP execution status.
            max_tool_turns: Maximum number of iterative tool calling turns to prevent infinite loops.
            is_comparison: Whether this is in dual-developer comparison mode.
            compare_users: Tuple of (user1, user2) when is_comparison is True.
        """
        # Ensure MCP client is connected
        if not mcp_client.connected:
            mcp_client.connect()

        # Prepare messages
        messages = self.prepare_messages(
            user_prompt,
            is_comparison=is_comparison,
            compare_users=compare_users
        )
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
                            &#9881; Calling MCP Tool: <b>{tc.tool_name}</b><br/>
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
