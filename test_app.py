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
    logger.info(" GitHubUser model validated successfully")

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
    logger.info(" Repository model validated successfully")

def test_helpers():
    logger.info("Testing utility helper functions...")
    assert format_number(None) == "0"
    assert format_number(0) == "0"
    assert format_number(950) == "950"
    assert format_number(1000) == "1k"
    assert format_number(12500) == "12.5k"
    assert format_number(1500000) == "1.5M"
    assert format_number(2000000) == "2M"
    assert format_number(10000000) == "10M"
    assert get_language_color("Python") == "#3572A5"
    assert get_language_color("TypeScript") == "#3178c6"
    logger.info(" Helper utilities validated successfully")

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

    from services.mcp_service import mcp_client, FALLBACK_TOOLS
    assert "search_issues" in mcp_client.tools
    search_tool = mcp_client.tools["search_issues"].to_openai_tool()
    assert search_tool["type"] == "function"
    assert "query" in search_tool["function"]["parameters"]["properties"]
    assert len(FALLBACK_TOOLS) >= 4
    logger.info(" MCP tool conversion to OpenAI function schema validated successfully")

def test_services():
    logger.info("Testing service imports and initialization...")
    from services import mcp_client, github_service, openai_service
    assert mcp_client is not None
    assert github_service is not None
    assert openai_service is not None
    assert len(mcp_client.tools) >= 17

    connected, status_label = openai_service.check_connection()
    assert isinstance(connected, bool)
    assert status_label in ("Connected", "Offline")
    logger.info(f" LLM Connection status checked: {status_label} (connected={connected})")
    logger.info(f" Services initialized. Available MCP tools count: {len(mcp_client.tools)}")

def test_comparison():
    logger.info("Testing comparison module and markdown dossier generator...")
    from ui import render_comparison_page
    from ui.comparison import generate_comparison_markdown
    from models import GitHubUser, RepoStats, DashboardMetrics
    assert callable(render_comparison_page)

    u1 = GitHubUser.model_validate({"login": "dev1", "name": "Developer One", "followers": 100})
    u2 = GitHubUser.model_validate({"login": "dev2", "name": "Developer Two", "followers": 200})
    s1 = RepoStats(total_repos=5, total_stars=1000, total_forks=100)
    s2 = RepoStats(total_repos=10, total_stars=500, total_forks=200)

    m1 = DashboardMetrics(user=u1, stats=s1, repos=[], orgs=[], language_breakdown=[], recent_activity=[])
    m2 = DashboardMetrics(user=u2, stats=s2, repos=[], orgs=[], language_breakdown=[], recent_activity=[])

    dossier = generate_comparison_markdown(m1, m2, ai_analysis="Analysis test")
    assert "@dev1" in dossier
    assert "@dev2" in dossier
    assert "Analysis test" in dossier
    assert "Head-to-Head Statistics" in dossier
    logger.info(" Comparison module and dossier generator validated successfully")

def main():
    logger.info("=== Starting Github Stalker pro Verification Tests ===")
    try:
        test_models()
        test_helpers()
        test_mcp_tools()
        test_services()
        test_comparison()
        logger.info("===  ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ===")
    except Exception as e:
        logger.error(f" Test verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
