from datetime import datetime
from typing import Any

# Standard GitHub language colors mapping
LANGUAGE_COLORS: dict[str, str] = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "Shell": "#89e051",
    "Vue": "#41b883",
    "Jupyter Notebook": "#DA5B0B",
    "Dockerfile": "#384d54",
}

def format_number(num: int | float | None) -> str:
    """Format large numbers into human-readable strings (e.g., 12.5k, 1.2M)."""
    if num is None:
        return "0"
    try:
        n = float(num)
        if n >= 1_000_000:
            val = f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".")
            return f"{val}M"
        if n >= 1_000:
            val = f"{n / 1_000:.1f}".rstrip("0").rstrip(".")
            return f"{val}k"
        return str(int(n))
    except (ValueError, TypeError):
        return "0"

def get_language_color(language: str | None) -> str:
    """Retrieve color HEX code for a given programming language."""
    if not language:
        return "#8a94a6"
    return LANGUAGE_COLORS.get(language, "#6e7681")

def format_error_message(error: Any) -> str:
    """Format various exception types and error structures into user-friendly strings."""
    if isinstance(error, str):
        return error
    if hasattr(error, "message") and getattr(error, "message"):
        return str(error.message)
    if hasattr(error, "response") and getattr(error, "response") is not None:
        try:
            resp_json = error.response.json()
            if "message" in resp_json:
                return f"API Error: {resp_json['message']}"
        except Exception:
            pass
        return f"HTTP Error {error.response.status_code}"
    return str(error)

def truncate_text(text: str | None, max_length: int = 120) -> str:
    """Truncate text to a maximum length with ellipses if needed."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3].rsplit(" ", 1)[0] + "..."

def format_timestamp(ts_str: str | None) -> str:
    """Parse ISO timestamp and format as human readable date."""
    if not ts_str:
        return "N/A"
    try:
        # Handle trailing Z or timezone offsets
        ts_clean = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_clean)
        return dt.strftime("%b %d, %Y")
    except Exception:
        return ts_str[:10] if len(ts_str) >= 10 else ts_str
