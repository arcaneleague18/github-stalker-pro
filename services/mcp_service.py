import json
import subprocess
import threading
import time
import requests
from typing import Any, Optional, Callable
from config import settings
from utils import get_logger, format_error_message
from models import MCPToolDefinition

logger = get_logger(__name__)

# Standard GitHub MCP Tool Definitions (for schema discovery and fallback routing)
STANDARD_GITHUB_MCP_TOOLS = [
    MCPToolDefinition(
        name="get_user",
        description="Get public profile information for a GitHub username.",
        inputSchema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "The GitHub username to look up."}
            },
            "required": ["username"]
        }
    ),
    MCPToolDefinition(
        name="list_user_repositories",
        description="List public repositories for a specific GitHub user.",
        inputSchema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "The GitHub username."},
                "sort": {"type": "string", "description": "Sort order (updated, stars, pushed).", "default": "updated"},
                "per_page": {"type": "integer", "description": "Number of repositories to return.", "default": 30}
            },
            "required": ["username"]
        }
    ),
    MCPToolDefinition(
        name="get_repository",
        description="Get detailed information about a specific GitHub repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "The repository owner (username or org)."},
                "repo": {"type": "string", "description": "The repository name."}
            },
            "required": ["owner", "repo"]
        }
    ),
    MCPToolDefinition(
        name="get_file_contents",
        description="Get the content of a file or README from a repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "The repository owner."},
                "repo": {"type": "string", "description": "The repository name."},
                "path": {"type": "string", "description": "File path (e.g., 'README.md', 'src/main.py')."}
            },
            "required": ["owner", "repo", "path"]
        }
    ),
    MCPToolDefinition(
        name="get_repository_tree",
        description="Get the file tree and directory structure of a repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "The repository owner."},
                "repo": {"type": "string", "description": "The repository name."},
                "tree_sha": {"type": "string", "description": "Branch name or commit SHA.", "default": "main"},
                "recursive": {"type": "boolean", "description": "Whether to fetch recursively.", "default": True}
            },
            "required": ["owner", "repo"]
        }
    ),
    MCPToolDefinition(
        name="list_commits",
        description="List recent commits for a GitHub repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "The repository owner."},
                "repo": {"type": "string", "description": "The repository name."},
                "per_page": {"type": "integer", "description": "Number of commits to return.", "default": 15}
            },
            "required": ["owner", "repo"]
        }
    ),
    MCPToolDefinition(
        name="list_branches",
        description="List branches for a GitHub repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "The repository owner."},
                "repo": {"type": "string", "description": "The repository name."}
            },
            "required": ["owner", "repo"]
        }
    ),
    MCPToolDefinition(
        name="list_pull_requests",
        description="List pull requests (open or closed) for a repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "The repository owner."},
                "repo": {"type": "string", "description": "The repository name."},
                "state": {"type": "string", "description": "PR state: open, closed, or all.", "default": "open"}
            },
            "required": ["owner", "repo"]
        }
    ),
    MCPToolDefinition(
        name="list_issues",
        description="List open issues for a GitHub repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "The repository owner."},
                "repo": {"type": "string", "description": "The repository name."},
                "state": {"type": "string", "description": "Issue state: open, closed, or all.", "default": "open"}
            },
            "required": ["owner", "repo"]
        }
    ),
    MCPToolDefinition(
        name="list_releases",
        description="List published releases for a GitHub repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "The repository owner."},
                "repo": {"type": "string", "description": "The repository name."}
            },
            "required": ["owner", "repo"]
        }
    ),
    MCPToolDefinition(
        name="get_user_contributions",
        description="Get total number of contributions (commits, issues, and PRs) for a GitHub user within a specified timeframe.",
        inputSchema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "The GitHub username"},
                "date_query": {"type": "string", "description": "The date search syntax (e.g. 2025-01-01..2025-12-31 or >2026-06-01)"}
            },
            "required": ["username", "date_query"]
        }
    ),
    MCPToolDefinition(
        name="list_tags",
        description="List git tags for a GitHub repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "The repository owner."},
                "repo": {"type": "string", "description": "The repository name."}
            },
            "required": ["owner", "repo"]
        }
    ),
    MCPToolDefinition(
        name="list_user_organizations",
        description="List public organizations for a specific GitHub user.",
        inputSchema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "The GitHub username."}
            },
            "required": ["username"]
        }
    ),
    MCPToolDefinition(
        name="list_user_activity",
        description="Get recent public activity events for a GitHub user.",
        inputSchema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "The GitHub username."},
                "per_page": {"type": "integer", "description": "Number of events to return.", "default": 15}
            },
            "required": ["username"]
        }
    ),
    MCPToolDefinition(
        name="list_user_followers",
        description="List the usernames of people who follow a specific GitHub user.",
        inputSchema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "The GitHub username."},
                "per_page": {"type": "integer", "description": "Number of followers to return (max 100).", "default": 30}
            },
            "required": ["username"]
        }
    ),
    MCPToolDefinition(
        name="list_user_following",
        description="List the usernames of people a specific GitHub user is following.",
        inputSchema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "The GitHub username."},
                "per_page": {"type": "integer", "description": "Number of followed users to return (max 100).", "default": 30}
            },
            "required": ["username"]
        }
    ),
    MCPToolDefinition(
        name="search_issues",
        description="Search issues and pull requests across GitHub repositories using query syntax (e.g., 'author:USERNAME type:issue' or 'author:USERNAME type:pr').",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query (e.g., 'author:torvalds type:pr' or 'repo:owner/repo is:open')."},
                "sort": {"type": "string", "description": "Sort field (comments, reactions, created, updated).", "default": "created"},
                "order": {"type": "string", "description": "Sort order (asc or desc).", "default": "desc"},
                "per_page": {"type": "integer", "description": "Number of results to return (max 100).", "default": 15}
            },
            "required": ["query"]
        }
    )
]

# Custom tools that fallback to HTTP REST adapter or extend standard stdio functionality
FALLBACK_TOOLS = [
    t for t in STANDARD_GITHUB_MCP_TOOLS
    if t.name in ("get_user_contributions", "list_user_followers", "list_user_following", "search_issues")
]

class MCPClient:
    """Manages connection and tool calling with the GitHub Model Context Protocol Server."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.connected: bool = False
        self.tools: dict[str, MCPToolDefinition] = {
            t.name: t for t in STANDARD_GITHUB_MCP_TOOLS
        }
        self.msg_id: int = 1
        self.lock = threading.Lock()
        self.status_callback: Optional[Callable[[str], None]] = None

    def register_status_callback(self, callback: Callable[[str], None]):
        """Register a callback function to report status updates to UI."""
        self.status_callback = callback

    def _notify(self, message: str):
        logger.info(message)
        if self.status_callback:
            try:
                self.status_callback(message)
            except Exception as e:
                logger.warning(f"Status callback failed: {e}")

    def connect(self) -> bool:
        """Connect to the GitHub MCP stdio server.
        Falls back to REST HTTP adapter if stdio server execution is unavailable locally.
        """
        if self.connected and self.process and self.process.poll() is None:
            return True

        command = settings.mcp_server_command
        pat = settings.get_github_pat()

        if not pat:
            logger.warning("No GitHub Personal Access Token configured. MCP server may experience rate limits.")

        logger.info(f"Attempting to start MCP server via stdio: {command}")
        self._notify(f"Connecting to GitHub MCP Server ({command})...")

        try:
            env = dict(os.environ if 'os' in globals() else {})
            import os
            env = os.environ.copy()
            if pat:
                env["GITHUB_PERSONAL_ACCESS_TOKEN"] = pat
                env["GITHUB_TOKEN"] = pat

            # Split command line cleanly for Windows/Unix
            import shlex
            cmd_args = shlex.split(command, posix=(os.name != "nt"))
            
            self.process = subprocess.Popen(
                cmd_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1
            )
            
            # Send MCP JSON-RPC 2.0 initialize request
            init_req = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"roots": {"listChanged": False}, "sampling": {}},
                    "clientInfo": {"name": "github-stalker-pro", "version": "1.0.0"}
                }
            }
            self._send_stdio(init_req)
            
            # Read initialization response
            resp = self._read_stdio(timeout=5.0)
            if resp and "result" in resp:
                self.connected = True
                self._notify("Connected to GitHub MCP stdio server successfully.")
                # Send initialized notification
                self._send_stdio({"jsonrpc": "2.0", "method": "notifications/initialized"})
                # Discover tools from stdio server
                self._discover_tools_stdio()
                return True
            else:
                logger.warning("No initialization response received from stdio MCP server. Switching to HTTP REST Adapter.")
        except Exception as e:
            logger.warning(f"Failed to launch stdio MCP server ({e}). Switching to high-resilience HTTP REST Adapter.")

        # High-resilience fallback: Use built-in REST adapter that implements MCP tool specifications over HTTP
        self.connected = True
        self._notify("Connected to GitHub MCP Server (HTTP Adapter Mode).")
        return True

    def disconnect(self):
        """Terminate the stdio MCP server if running."""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
        self.connected = False
        self.process = None

    def _get_next_id(self) -> int:
        with self.lock:
            current = self.msg_id
            self.msg_id += 1
            return current

    def _send_stdio(self, payload: dict[str, Any]):
        if not self.process or not self.process.stdin:
            return
        line = json.dumps(payload) + "\n"
        self.process.stdin.write(line)
        self.process.stdin.flush()

    def _read_stdio(self, timeout: float = 5.0) -> Optional[dict[str, Any]]:
        if not self.process or not self.process.stdout:
            return None
        start_time = time.time()
        while time.time() - start_time < timeout:
            line = self.process.stdout.readline()
            if line:
                line = line.strip()
                if not line:
                    continue
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
            time.sleep(0.05)
        return None

    def _discover_tools_stdio(self):
        """Query tools/list from stdio MCP server."""
        req = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list",
            "params": {}
        }
        self._send_stdio(req)
        resp = self._read_stdio(timeout=5.0)
        if resp and "result" in resp and "tools" in resp["result"]:
            for t in resp["result"]["tools"]:
                name = t.get("name")
                if name:
                    self.tools[name] = MCPToolDefinition(
                        name=name,
                        description=t.get("description", ""),
                        inputSchema=t.get("inputSchema", {})
                    )
            
            # Inject custom Python-adapter tools that standard stdio server lacks
            for fallback in FALLBACK_TOOLS:
                if fallback.name not in self.tools:
                    self.tools[fallback.name] = fallback

    def get_openai_tools(self) -> list[dict[str, Any]]:
        """Return all available MCP tools formatted as OpenAI function specifications."""
        return [t.to_openai_tool() for t in self.tools.values()]

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute an MCP tool by name with arguments.
        Routes to stdio MCP process if active, or executes standard GitHub API adapter.
        """
        self._notify(f"Executing MCP tool `{tool_name}`...")
        logger.info(f"MCP Call: {tool_name} with args: {arguments}")

        # 1. Intercept custom tools that stdio does not support natively
        if tool_name in ("get_user_contributions", "list_user_followers", "list_user_following", "search_issues"):
            return self._execute_rest_adapter(tool_name, arguments)

        # 2. Try stdio if connected and process active
        if self.process and self.process.poll() is None:
            req = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments}
            }
            try:
                self._send_stdio(req)
                resp = self._read_stdio(timeout=10.0)
                if resp and "result" in resp:
                    content_list = resp["result"].get("content", [])
                    texts = [c.get("text", "") for c in content_list if c.get("type") == "text"]
                    return "\n".join(texts) if texts else json.dumps(resp["result"])
            except Exception as e:
                logger.warning(f"Stdio tool call failed ({e}). Falling back to HTTP REST adapter.")

        # 3. High-resilience REST adapter execution
        return self._execute_rest_adapter(tool_name, arguments)

    def _execute_rest_adapter(self, tool_name: str, args: dict[str, Any]) -> str:
        """Fallback adapter executing MCP tool schemas directly via GitHub REST API."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        pat = settings.get_github_pat()
        if pat:
            headers["Authorization"] = f"token {pat}"

        base_url = "https://api.github.com"
        
        try:
            if tool_name == "get_user_contributions":
                username = args.get("username", "")
                date_query = args.get("date_query", "")
                
                # Fetch Commits
                commit_headers = headers.copy()
                commit_headers["Accept"] = "application/vnd.github.cloak-preview+json"
                commit_url = f"{base_url}/search/commits?q=author:{username}+committer-date:{date_query}"
                commit_res = requests.get(commit_url, headers=commit_headers, timeout=10)
                commit_res.raise_for_status()
                commits_count = commit_res.json().get("total_count", 0)

                # Fetch Issues
                issue_url = f"{base_url}/search/issues?q=author:{username}+created:{date_query}+type:issue"
                issue_res = requests.get(issue_url, headers=headers, timeout=10)
                issue_res.raise_for_status()
                issues_count = issue_res.json().get("total_count", 0)

                # Fetch Pull Requests
                pr_url = f"{base_url}/search/issues?q=author:{username}+created:{date_query}+type:pr"
                pr_res = requests.get(pr_url, headers=headers, timeout=10)
                pr_res.raise_for_status()
                prs_count = pr_res.json().get("total_count", 0)

                return json.dumps({
                    "commits": commits_count,
                    "issues_opened": issues_count,
                    "pull_requests_opened": prs_count,
                    "total_contributions": commits_count + issues_count + prs_count,
                    "query_details": {
                        "username": username,
                        "date_query": date_query
                    }
                }, indent=2)

            elif tool_name == "get_user":
                url = f"{base_url}/users/{args['username']}"
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 404:
                    return f"User '{args['username']}' not found on GitHub."
                res.raise_for_status()
                return json.dumps(res.json(), indent=2)

            elif tool_name in ["list_user_repositories", "search_repositories"]:
                username = args.get("username") or args.get("query", "")
                sort = args.get("sort", "updated")
                per_page = args.get("per_page", 30)
                url = f"{base_url}/users/{username}/repos?sort={sort}&per_page={per_page}"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                repos = res.json()
                summary = [
                    {
                        "name": r.get("name"),
                        "full_name": r.get("full_name"),
                        "description": r.get("description"),
                        "stars": r.get("stargazers_count"),
                        "forks": r.get("forks_count"),
                        "language": r.get("language"),
                        "url": r.get("html_url")
                    } for r in repos
                ]
                return json.dumps(summary, indent=2)

            elif tool_name == "get_repository":
                url = f"{base_url}/repos/{args['owner']}/{args['repo']}"
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 404:
                    return f"Repository '{args['owner']}/{args['repo']}' not found."
                res.raise_for_status()
                return json.dumps(res.json(), indent=2)

            elif tool_name == "get_file_contents":
                url = f"{base_url}/repos/{args['owner']}/{args['repo']}/contents/{args['path']}"
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 404:
                    return f"File '{args['path']}' not found in '{args['owner']}/{args['repo']}'."
                res.raise_for_status()
                data = res.json()
                if "content" in data and data.get("encoding") == "base64":
                    import base64
                    decoded = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                    return decoded
                return json.dumps(data, indent=2)

            elif tool_name == "get_repository_tree":
                tree_sha = args.get("tree_sha", "main")
                recursive = "1" if args.get("recursive", True) else "0"
                url = f"{base_url}/repos/{args['owner']}/{args['repo']}/git/trees/{tree_sha}?recursive={recursive}"
                res = requests.get(url, headers=headers, timeout=10)
                # If default main branch returns 404, fallback to master
                if res.status_code == 404 and tree_sha == "main":
                    fallback_url = f"{base_url}/repos/{args['owner']}/{args['repo']}/git/trees/master?recursive={recursive}"
                    fallback_res = requests.get(fallback_url, headers=headers, timeout=10)
                    if fallback_res.status_code == 200:
                        res = fallback_res
                res.raise_for_status()
                tree_data = res.json().get("tree", [])
                paths = [f"{t['type'][:4]} | {t['path']}" for t in tree_data[:100]]
                return "First 100 entries in repository tree:\n" + "\n".join(paths)

            elif tool_name == "list_commits":
                per_page = args.get("per_page", 15)
                url = f"{base_url}/repos/{args['owner']}/{args['repo']}/commits?per_page={per_page}"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                commits = res.json()
                summary = [
                    {
                        "sha": c.get("sha", "")[:7],
                        "author": c.get("commit", {}).get("author", {}).get("name"),
                        "date": c.get("commit", {}).get("author", {}).get("date"),
                        "message": c.get("commit", {}).get("message", "").split("\n")[0]
                    } for c in commits
                ]
                return json.dumps(summary, indent=2)

            elif tool_name == "list_branches":
                url = f"{base_url}/repos/{args['owner']}/{args['repo']}/branches"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                branches = [b.get("name") for b in res.json()]
                return json.dumps(branches, indent=2)

            elif tool_name == "list_pull_requests":
                state = args.get("state", "open")
                url = f"{base_url}/repos/{args['owner']}/{args['repo']}/pulls?state={state}"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                prs = res.json()
                summary = [
                    {
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "state": pr.get("state"),
                        "user": pr.get("user", {}).get("login")
                    } for pr in prs
                ]
                return json.dumps(summary, indent=2)

            elif tool_name == "list_issues":
                state = args.get("state", "open")
                url = f"{base_url}/repos/{args['owner']}/{args['repo']}/issues?state={state}"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                issues = [i for i in res.json() if "pull_request" not in i]
                summary = [
                    {
                        "number": i.get("number"),
                        "title": i.get("title"),
                        "state": i.get("state"),
                        "comments": i.get("comments")
                    } for i in issues
                ]
                return json.dumps(summary, indent=2)

            elif tool_name == "list_releases":
                url = f"{base_url}/repos/{args['owner']}/{args['repo']}/releases"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                releases = [r.get("tag_name") for r in res.json()]
                return json.dumps(releases, indent=2)

            elif tool_name == "list_tags":
                url = f"{base_url}/repos/{args['owner']}/{args['repo']}/tags"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                tags = [t.get("name") for t in res.json()]
                return json.dumps(tags, indent=2)

            elif tool_name == "list_user_organizations":
                url = f"{base_url}/users/{args['username']}/orgs"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                orgs = [{"login": o.get("login"), "description": o.get("description")} for o in res.json()]
                return json.dumps(orgs, indent=2)

            elif tool_name == "list_user_activity":
                per_page = args.get("per_page", 15)
                url = f"{base_url}/users/{args['username']}/events/public?per_page={per_page}"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                events = res.json()
                summary = [
                    {
                        "type": e.get("type"),
                        "repo": e.get("repo", {}).get("name"),
                        "created_at": e.get("created_at")
                    } for e in events
                ]
                return json.dumps(summary, indent=2)

            elif tool_name == "list_user_followers":
                per_page = args.get("per_page", 30)
                url = f"{base_url}/users/{args['username']}/followers?per_page={per_page}"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                followers = [
                    {
                        "username": u.get("login"),
                        "profile_url": u.get("html_url"),
                        "avatar_url": u.get("avatar_url")
                    } for u in res.json()
                ]
                return json.dumps(followers, indent=2)

            elif tool_name == "list_user_following":
                per_page = args.get("per_page", 30)
                url = f"{base_url}/users/{args['username']}/following?per_page={per_page}"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                following = [
                    {
                        "username": u.get("login"),
                        "profile_url": u.get("html_url"),
                        "avatar_url": u.get("avatar_url")
                    } for u in res.json()
                ]
                return json.dumps(following, indent=2)

            elif tool_name == "search_issues":
                query = args.get("query", "")
                sort = args.get("sort", "created")
                order = args.get("order", "desc")
                per_page = args.get("per_page", 15)
                url = f"{base_url}/search/issues?q={query}&sort={sort}&order={order}&per_page={per_page}"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                data = res.json()
                items = data.get("items", [])
                summary = [
                    {
                        "number": item.get("number"),
                        "title": item.get("title"),
                        "state": item.get("state"),
                        "url": item.get("html_url"),
                        "author": item.get("user", {}).get("login"),
                        "created_at": item.get("created_at"),
                        "comments": item.get("comments", 0),
                        "is_pr": "pull_request" in item
                    } for item in items
                ]
                return json.dumps({
                    "total_count": data.get("total_count", 0),
                    "items": summary
                }, indent=2)

            else:
                return f"Error: Tool '{tool_name}' is not recognized by the MCP server."
        except requests.exceptions.HTTPError as e:
            return f"GitHub API Error for tool '{tool_name}': {format_error_message(e)}"
        except Exception as e:
            return f"Execution error for tool '{tool_name}': {str(e)}"

# Global MCP client instance
mcp_client = MCPClient()
