import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file if it exists
load_dotenv(override=True)

class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""
    
    # LLM API settings (OpenRouter)
    openrouter_api_key: Optional[SecretStr] = Field(default=None, alias="OPENROUTER_API_KEY")
    openai_base_url: Optional[str] = Field(default="https://openrouter.ai/api/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="openai/gpt-oss-20b:free", alias="OPENAI_MODEL")
    
    # GitHub credentials
    github_pat: Optional[SecretStr] = Field(default=None, alias="GITHUB_PERSONAL_ACCESS_TOKEN")
    
    # MCP configuration
    mcp_server_command: str = Field(
        default="npx -y @modelcontextprotocol/server-github",
        alias="MCP_SERVER_COMMAND"
    )
    
    # App Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_title: str = Field(default="GitHub Insight AI", alias="APP_TITLE")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_openai_api_key(self) -> str:
        """Safe getter for LLM API Key (OPENROUTER_API_KEY)."""
        if self.openrouter_api_key:
            return self.openrouter_api_key.get_secret_value()
        return os.environ.get("OPENROUTER_API_KEY", "")

    def get_base_url(self) -> str:
        """Get API base URL."""
        return self.openai_base_url or os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

    def get_github_pat(self) -> str:
        """Safe getter for GitHub Personal Access Token."""
        if not self.github_pat:
            return os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        return self.github_pat.get_secret_value()

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate if required configuration settings are present."""
        errors = []
        if not self.get_openai_api_key():
            errors.append("LLM API Key is missing. Please set OPENROUTER_API_KEY in your .env file.")
        if not self.get_github_pat():
            errors.append("GITHUB_PERSONAL_ACCESS_TOKEN is missing. Please set it in your .env file or environment.")
        return len(errors) == 0, errors

# Global configuration instance
settings = Settings()
