import json
from typing import Optional
from utils import get_logger, get_language_color
from models import (
    GitHubUser,
    Repository,
    RepoStats,
    LanguageDistribution,
    ActivityEvent,
    DashboardMetrics,
    Organization
)
from .mcp_service import mcp_client

logger = get_logger(__name__)

class GitHubService:
    """High-level domain service for GitHub account aggregation and metrics.
    Built on top of MCP tool calls and includes in-memory session caching.
    """

    def __init__(self):
        # In-memory cache for the duration of the application session
        self._cache: dict[str, DashboardMetrics] = {}

    def get_dashboard_metrics(self, username: str, force_refresh: bool = False) -> Optional[DashboardMetrics]:
        """Fetch and aggregate complete dashboard metrics for a GitHub user.
        Uses cached results unless force_refresh is requested.
        """
        username_clean = username.strip().lower()
        if not force_refresh and username_clean in self._cache:
            logger.info(f"Returning cached dashboard metrics for user '{username_clean}'")
            return self._cache[username_clean]

        logger.info(f"Aggregating dashboard metrics via MCP tools for user '{username_clean}'")
        
        # 1. Fetch User Profile via MCP
        user_json_str = mcp_client.call_tool("get_user", {"username": username_clean})
        try:
            user_data = json.loads(user_json_str)
            if "login" not in user_data:
                logger.warning(f"User '{username_clean}' not found: {user_json_str}")
                return None
            user = GitHubUser.model_validate(user_data)
        except Exception as e:
            logger.error(f"Failed to parse user profile for '{username_clean}': {e}")
            return None

        # 2. Fetch User Repositories via MCP
        repos_json_str = mcp_client.call_tool("list_user_repositories", {"username": username_clean, "per_page": 100})
        repos: list[Repository] = []
        try:
            repos_data = json.loads(repos_json_str)
            if isinstance(repos_data, list):
                for r in repos_data:
                    # Translate MCP summary fields if needed
                    repo_dict = {
                        "id": r.get("id", abs(hash(r.get("name", "")))),
                        "name": r.get("name", ""),
                        "full_name": r.get("full_name", f"{username_clean}/{r.get('name', '')}"),
                        "description": r.get("description"),
                        "stargazers_count": r.get("stars", r.get("stargazers_count", 0)),
                        "forks_count": r.get("forks", r.get("forks_count", 0)),
                        "language": r.get("language"),
                        "html_url": r.get("url", r.get("html_url"))
                    }
                    repos.append(Repository.model_validate(repo_dict))
        except Exception as e:
            logger.warning(f"Could not parse repositories list: {e}")

        # 3. Compute Repository Statistics & Language Breakdown
        total_stars = sum(r.stargazers_count for r in repos)
        total_forks = sum(r.forks_count for r in repos)
        
        lang_counts: dict[str, int] = {}
        for r in repos:
            if r.language:
                lang_counts[r.language] = lang_counts.get(r.language, 0) + 1

        total_lang_repos = sum(lang_counts.values()) or 1
        lang_breakdown: list[LanguageDistribution] = []
        for lang, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round((count / total_lang_repos) * 100, 1)
            lang_breakdown.append(
                LanguageDistribution(
                    language=lang,
                    count=count,
                    percentage=pct,
                    color=get_language_color(lang)
                )
            )

        # Top repositories sorted by stars
        top_repos = sorted(repos, key=lambda x: x.stargazers_count, reverse=True)[:6]

        stats = RepoStats(
            total_repos=len(repos),
            total_stars=total_stars,
            total_forks=total_forks,
            languages=lang_counts,
            top_repos=top_repos
        )

        # 4. Fetch Organizations via MCP
        orgs: list[Organization] = []
        orgs_json_str = mcp_client.call_tool("list_user_organizations", {"username": username_clean})
        try:
            orgs_data = json.loads(orgs_json_str)
            if isinstance(orgs_data, list):
                for idx, o in enumerate(orgs_data):
                    orgs.append(
                        Organization(
                            login=o.get("login", ""),
                            id=o.get("id", idx),
                            description=o.get("description")
                        )
                    )
        except Exception:
            pass

        # 5. Fetch Recent Activity via MCP
        activity: list[ActivityEvent] = []
        act_json_str = mcp_client.call_tool("list_user_activity", {"username": username_clean, "per_page": 10})
        try:
            act_data = json.loads(act_json_str)
            if isinstance(act_data, list):
                for idx, a in enumerate(act_data):
                    activity.append(
                        ActivityEvent(
                            id=str(idx),
                            type=a.get("type", "Event"),
                            repo={"name": a.get("repo", "repository")},
                            created_at=a.get("created_at")
                        )
                    )
        except Exception:
            pass

        metrics = DashboardMetrics(
            user=user,
            orgs=orgs,
            repos=repos,
            stats=stats,
            language_breakdown=lang_breakdown,
            recent_activity=activity
        )

        # Save to session cache
        self._cache[username_clean] = metrics
        return metrics

    def clear_cache(self, username: Optional[str] = None):
        """Clear cached metrics for a specific user or all users."""
        if username:
            self._cache.pop(username.strip().lower(), None)
        else:
            self._cache.clear()

# Global GitHub service instance
github_service = GitHubService()
