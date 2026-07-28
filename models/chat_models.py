from typing import Any, Optional
from pydantic import BaseModel, Field

class ToolCallLog(BaseModel):
    """Represents an execution log of an MCP tool during chat streaming."""
    id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Optional[str] = None
    status: str = "running"  # running, success, error
    error_message: Optional[str] = None

class ChatMessage(BaseModel):
    """Represents a single chat message in the conversation history."""
    role: str  # "user", "assistant", "system", or "tool"
    content: str
    tool_calls: list[ToolCallLog] = Field(default_factory=list)
    timestamp: Optional[str] = None

    model_config = {"extra": "ignore"}

class MCPToolDefinition(BaseModel):
    """Schema definition for a Model Context Protocol tool exposed to OpenAI."""
    name: str
    description: str
    inputSchema: dict[str, Any] = Field(default_factory=dict)

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert MCP tool definition to standard OpenAI function tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.inputSchema
            }
        }

class SessionStateData(BaseModel):
    """Structured representation of active session state keys."""
    current_username: Optional[str] = None
    selected_repository: Optional[str] = None
    messages: list[ChatMessage] = Field(default_factory=list)
    mcp_status: str = "Disconnected"
    error_notification: Optional[str] = None
