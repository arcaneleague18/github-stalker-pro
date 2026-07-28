from typing import Any, Generator, Optional
import openai
from openai.types.chat import ChatCompletionChunk
from config import settings
from utils import get_logger, format_error_message
from models import ToolCallLog

logger = get_logger(__name__)

class OpenAIService:
    """Manages communication, streaming, and tool calling with the OpenAI API."""

    def __init__(self):
        self._client: Optional[openai.OpenAI] = None

    def get_client(self) -> openai.OpenAI:
        """Initialize and return the OpenAI/OpenRouter client."""
        if self._client is None:
            api_key = settings.get_openai_api_key()
            if not api_key:
                raise ValueError("API Key is missing. Please set OPENROUTER_API_KEY in your .env file.")
            
            base_url = settings.get_base_url()
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
                client_kwargs["default_headers"] = {
                    "HTTP-Referer": "https://github.com/github-insight-ai",
                    "X-Title": "GitHub Insight AI"
                }
                logger.info(f"Configured OpenAI/OpenRouter client with base URL: {base_url}")
            
            self._client = openai.OpenAI(**client_kwargs)
        return self._client

    def stream_chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: Optional[str] = None
    ) -> Generator[str | list[ToolCallLog], None, None]:
        """Stream a chat completion response from OpenAI with MCP tool calling support.
        
        Yields:
            str: Text chunks as they arrive from the streaming response.
            list[ToolCallLog]: When the model requests tool execution, yields a list of tool call objects.
        """
        client = self.get_client()
        target_model = model or settings.openai_model

        logger.info(f"Initiating OpenAI stream using model '{target_model}' with {len(tools)} available MCP tools")

        try:
            # Prepare arguments; omit tools parameter if list is empty
            kwargs = {
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
                logger.info(f"OpenAI model generated {len(tool_logs)} MCP tool call request(s)")
                yield tool_logs

        except openai.AuthenticationError:
            yield "\n\n❌ **Authentication Error:** Invalid OpenAI API Key. Please verify `OPENAI_API_KEY` in your `.env` file."
        except openai.RateLimitError:
            yield "\n\n⏳ **Rate Limit Exceeded:** You have hit the rate limit or quota for your OpenAI account. Please try again later."
        except openai.NotFoundError:
            # Fallback if specific model like gpt-5.5 is not available to the user yet
            if target_model != "gpt-4o":
                logger.warning(f"Model '{target_model}' not found or unavailable. Falling back to 'gpt-4o'")
                yield f"\n\n⚠️ *Model `{target_model}` unavailable. Automatically falling back to `gpt-4o`...*\n\n"
                yield from self.stream_chat_with_tools(messages, tools, model="gpt-4o")
            else:
                yield f"\n\n❌ **Model Error:** The requested OpenAI model `{target_model}` was not found."
        except openai.APIConnectionError:
            yield "\n\n🌐 **Network Error:** Could not connect to OpenAI API. Please check your internet connection."
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"\n\n❌ **An unexpected error occurred:** {format_error_message(e)}"

# Global OpenAI service instance
openai_service = OpenAIService()
