"""Verification script for Github Stalker pro models, configuration, and services."""
import sys
from utils import get_logger, format_number, get_language_color
from models import GitHubUser, Repository, RepoStats, MCPToolDefinition
from config import settings

logger = get_logger("test_app")

def test_models():
    logger.info("Testing Pydantic models...")
    user_data = {
        "login": "octocat",
        "name": "The Octocat",
        "public_repos": 8,
        "followers": 12000,
        "following": 9
    }
    user = GitHubUser.model_validate(user_data)
    assert user.display_name == "The Octocat"
    assert user.public_repos == 8
    logger.info("✅ GitHubUser model validated successfully")

    repo_data = {
        "id": 12345,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "stargazers_count": 2500,
        "forks_count": 500,
        "language": "Python"
    }
    repo = Repository.model_validate(repo_data)
    assert repo.name == "Hello-World"
    assert repo.stargazers_count == 2500
    logger.info("✅ Repository model validated successfully")

def test_helpers():
    logger.info("Testing utility helper functions...")
    assert format_number(12500) == "12.5k"
    assert format_number(1500000) == "1.5M"
    assert get_language_color("Python") == "#3572A5"
    logger.info("✅ Helper utilities validated successfully")

def test_mcp_tools():
    logger.info("Testing MCP tool definition conversion...")
    tool = MCPToolDefinition(
        name="test_tool",
        description="A test tool",
        inputSchema={"type": "object", "properties": {"arg1": {"type": "string"}}}
    )
    openai_tool = tool.to_openai_tool()
    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == "test_tool"
    logger.info("✅ MCP tool conversion to OpenAI function schema validated successfully")

def test_services():
    logger.info("Testing service imports and initialization...")
    from services import mcp_client, github_service, openai_service
    assert mcp_client is not None
    assert github_service is not None
    assert openai_service is not None
    logger.info(f"✅ Services initialized. Available MCP tools count: {len(mcp_client.tools)}")

def main():
    logger.info("=== Starting Github Stalker pro Verification Tests ===")
    try:
        test_models()
        test_helpers()
        test_mcp_tools()
        test_services()
        logger.info("=== 🎉 ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ===")
    except Exception as e:
        logger.error(f"❌ Test verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
