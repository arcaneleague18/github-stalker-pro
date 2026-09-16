from typing import Any, Generator, Optional
import openai
from openai.types.chat import ChatCompletionChunk
from config import settings
from utils import get_logger, format_error_message
from models import ToolCallLog

logger = get_logger(__name__)

class OpenAIService:
    """Manages communication, streaming, and tool calling with the local LLM proxy."""

    def __init__(self):
        self._client: Optional[openai.OpenAI] = None
        self._last_check_time: float = 0
        self._last_status: tuple[bool, str] = (False, "Offline")

    def get_client(self) -> openai.OpenAI:
        """Initialize and return the OpenAI-compatible client pointing to the local model proxy."""
        if self._client is None:
            base_url = settings.get_base_url()
            logger.info(f"Configured LLM client with local model proxy at: {base_url}")
            
            self._client = openai.OpenAI(
                api_key="not-needed",
                base_url=base_url
            )
        return self._client

    def check_connection(self) -> tuple[bool, str]:
        """Check if the LLM API / proxy is reachable with cached result."""
        import time
        now = time.time()
        if now - self._last_check_time < 8.0:
            return self._last_status

        try:
            client = self.get_client()
            client.models.list(timeout=2.0)
            self._last_status = (True, "Connected")
        except Exception as e:
            logger.debug(f"LLM connection check failed: {e}")
            self._last_status = (False, "Offline")

        self._last_check_time = now
        return self._last_status

    def stream_chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        model: Optional[str] = None
    ) -> Generator[str | list[ToolCallLog], None, None]:
        """Stream a chat completion response from the local LLM with MCP tool calling support.
        
        Yields:
            str: Text chunks as they arrive from the streaming response.
            list[ToolCallLog]: When the model requests tool execution, yields a list of tool call objects.
        """
        try:
            client = self.get_client()
            target_model = model or settings.openai_model
            num_tools = len(tools) if tools is not None else 0

            logger.info(f"Initiating LLM stream using model '{target_model}' with {num_tools} available MCP tools")

            # Prepare arguments; omit tools parameter if list is empty or None
            kwargs: dict[str, Any] = {
                "model": target_model,
                "messages": messages,
                "stream": True,
                "temperature": 0.3
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response_stream = client.chat.completions.create(**kwargs)

            # State tracking for streaming tool calls
            accumulated_tool_calls: dict[int, dict[str, Any]] = {}
            has_tool_calls = False

            for chunk in response_stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # Yield streaming text content directly to UI renderer
                if delta.content:
                    yield delta.content

                # Accumulate tool call chunks
                if delta.tool_calls:
                    has_tool_calls = True
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": tc.id or f"call_{idx}",
                                "name": tc.function.name if tc.function and tc.function.name else "",
                                "arguments": ""
                            }
                        if tc.function and tc.function.name and not accumulated_tool_calls[idx]["name"]:
                            accumulated_tool_calls[idx]["name"] = tc.function.name
                        if tc.function and tc.function.arguments:
                            accumulated_tool_calls[idx]["arguments"] += tc.function.arguments

            # If tool calls were accumulated, parse arguments and yield tool call logs
            if has_tool_calls and accumulated_tool_calls:
                tool_logs: list[ToolCallLog] = []
                import json
                for idx, tc_data in sorted(accumulated_tool_calls.items()):
                    args_str = tc_data["arguments"]
                    try:
                        args_dict = json.loads(args_str) if args_str else {}
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse JSON arguments for tool call '{tc_data['name']}': {args_str}")
                        args_dict = {"raw_arguments": args_str}

                    tool_logs.append(
                        ToolCallLog(
                            id=tc_data["id"],
                            tool_name=tc_data["name"],
                            arguments=args_dict,
                            status="running"
                        )
                    )
                logger.info(f"LLM generated {len(tool_logs)} MCP tool call request(s)")
                yield tool_logs

        except openai.AuthenticationError:
            yield "\n\n**Authentication Error:** The local model proxy rejected the request. Check your proxy configuration."
        except openai.RateLimitError:
            yield "\n\n**Rate Limit Exceeded:** The model proxy rate limited the request. Please try again later."
        except openai.APIConnectionError:
            yield "\n\n**Connection Error:** Could not connect to the local model proxy at " + settings.get_base_url() + ". Make sure it is running."
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            yield f"\n\n**An unexpected error occurred:** {format_error_message(e)}"

# Global OpenAI service instance
openai_service = OpenAIService()
