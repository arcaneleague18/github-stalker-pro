from typing import Optional, Any
from pydantic import BaseModel, Field

class GitHubUser(BaseModel):
    """Represents a GitHub user profile."""
    login: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    blog: Optional[str] = None
    twitter_username: Optional[str] = None
    public_repos: int = 0
    public_gists: int = 0
    followers: int = 0
    following: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"extra": "ignore"}

    @property
    def display_name(self) -> str:
        return self.name or self.login

class Organization(BaseModel):
    """Represents a GitHub organization membership."""
    login: str
    id: int
    avatar_url: Optional[str] = None
    description: Optional[str] = None

    model_config = {"extra": "ignore"}

class Repository(BaseModel):
    """Represents a GitHub repository."""
    id: int
    name: str
    full_name: str
    private: bool = False
    html_url: Optional[str] = None
    description: Optional[str] = None
    fork: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None
    homepage: Optional[str] = None
    size: int = 0
    stargazers_count: int = 0
    watchers_count: int = 0
    language: Optional[str] = None
    forks_count: int = 0
    open_issues_count: int = 0
    default_branch: str = "main"
    topics: list[str] = Field(default_factory=list)
    archived: bool = False
    disabled: bool = False

    model_config = {"extra": "ignore"}

class RepoStats(BaseModel):
    """Summary statistics across a user's repositories."""
    total_repos: int = 0
    total_stars: int = 0
    total_forks: int = 0
    total_open_issues: int = 0
    languages: dict[str, int] = Field(default_factory=dict)
    top_repos: list[Repository] = Field(default_factory=list)

class LanguageDistribution(BaseModel):
    """Programming language distribution metric."""
    language: str
    count: int
    percentage: float
    color: str

class ActivityEvent(BaseModel):
    """Represents a public GitHub event/activity."""
    id: str
    type: str
    actor: dict[str, Any] = Field(default_factory=dict)
    repo: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None

    model_config = {"extra": "ignore"}

    @property
    def action_summary(self) -> str:
        repo_name = self.repo.get("name", "unknown/repo")
        if self.type == "PushEvent":
            commits = self.payload.get("commits", [])
            return f"Pushed {len(commits)} commit(s) to {repo_name}"
        elif self.type == "CreateEvent":
            ref_type = self.payload.get("ref_type", "repository")
            return f"Created {ref_type} in {repo_name}"
        elif self.type == "WatchEvent":
            return f"Starred repository {repo_name}"
        elif self.type == "ForkEvent":
            return f"Forked repository {repo_name}"
        elif self.type == "IssuesEvent":
            action = self.payload.get("action", "modified")
            return f"{action.capitalize()} issue in {repo_name}"
        elif self.type == "PullRequestEvent":
            action = self.payload.get("action", "modified")
            return f"{action.capitalize()} pull request in {repo_name}"
        return f"{self.type.replace('Event', '')} on {repo_name}"

class DashboardMetrics(BaseModel):
    """Aggregated metrics for dashboard rendering."""
    user: GitHubUser
    orgs: list[Organization] = Field(default_factory=list)
    repos: list[Repository] = Field(default_factory=list)
    stats: RepoStats
    language_breakdown: list[LanguageDistribution] = Field(default_factory=list)
    recent_activity: list[ActivityEvent] = Field(default_factory=list)
