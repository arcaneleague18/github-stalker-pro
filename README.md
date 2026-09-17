# 🤖 Github Stalker pro

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-FF4B4B.svg)](https://streamlit.io)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Enabled-8A2BE2.svg)](https://modelcontextprotocol.io)
[![OpenAI Responses API](https://img.shields.io/badge/OpenAI-GPT--5.5-412991.svg)](https://openai.com)

**Github Stalker pro** is a production-quality AI web application built with Streamlit that allows developers to enter any public GitHub username and chat with an AI assistant capable of answering deep architectural and software engineering questions about that account.

Unlike traditional AI applications,it dynamically connects to the **GitHub MCP (Model Context Protocol) Server**, allowing the OpenAI model to autonomously invoke tools in real-time to inspect repository trees, read source code, analyze READMEs, and review commits.

---

## ✨ Features

- **🎯 Zero-RAG Architecture:** Eliminates outdated embeddings and vector syncing by dynamically querying live GitHub data via Model Context Protocol tool calling.
- **📊 Rich Analytics Dashboard:**
  - Premium Dark Theme with glassmorphism UI cards and glowing gradients.
  - Interactive profile banner displaying followers, company, location, and website.
  - Altair-powered programming language distribution charts and badges.
  - Top repository cards with star/fork statistics and **"⚡ Focus in Chat"** buttons to lock AI context to a specific repository.
- **💬 Deep ChatGPT-Style Conversation Interface:**
  - Real-time response streaming from OpenAI Responses API.
  - Expandable **MCP Tool Execution Logs** allowing you to inspect exact JSON arguments and outputs returned by GitHub tools.
  - Auto-scroll, syntax-highlighted code blocks, and markdown rendering.
  - Interactive **Suggested AI Prompts** (e.g., *"Explain the architecture of their largest project"*, *"Which repositories contain Docker?"*).
- **🛡️ High-Resilience MCP Client:** Supports standard stdio JSON-RPC 2.0 communication (`@modelcontextprotocol/server-github` via `npx` or Docker) with an intelligent built-in HTTP REST adapter fallback.
- **⚡ In-Memory Session Caching:** Caches static profile metrics during Streamlit sessions to prevent unnecessary API calls and rate-limiting.

---

## 🏗️ Architecture

```mermaid
flowchart TD

subgraph group_presentation["Streamlit UI"]
  node_app["Streamlit App<br/>entry point<br/>[app.py]"]
  node_dashboard["Dashboard<br/>UI component<br/>[dashboard.py]"]
  node_comparison_ui["Comparison Views<br/>UI component<br/>[comparison.py]"]
  node_sidebar["Sidebar<br/>UI component<br/>[sidebar.py]"]
  node_chat_ui["Chat View<br/>UI component<br/>[chat.py]"]
  node_styles["Local Stylesheet<br/>theme asset<br/>[styles.css]"]
  node_comparison_chat["Comparison Chat<br/>UI component<br/>[comparison_chat.py]"]
end

subgraph group_application["Application Services"]
  node_github_service["GitHub Service<br/>domain service<br/>[github_service.py]"]
  node_chat_service["Chat Orchestrator<br/>conversation service<br/>[chat_service.py]"]
  node_session["Session Service<br/>state manager<br/>[session_service.py]"]
end

subgraph group_domain["State &amp; Models"]
  node_github_models["GitHub Models<br/>domain schemas<br/>[github_models.py]"]
  node_chat_models["Chat Models<br/>domain schemas<br/>[chat_models.py]"]
end

subgraph group_integrations["AI &amp; GitHub Integrations"]
  node_config["Environment Config<br/>configuration<br/>[config.py]"]
  node_openai_service["OpenAI Service<br/>AI client<br/>[openai_service.py]"]
  node_mcp_service["MCP Service<br/>tool transport<br/>[mcp_service.py]"]
  node_openai_api{{"OpenAI-Compatible API<br/>external AI API"}}
  node_mcp_server{{"GitHub MCP Server<br/>child process"}}
  node_github_api{{"GitHub HTTP API<br/>external API"}}
end

node_app -->|"composes"| node_dashboard
node_app -->|"composes"| node_comparison_ui
node_app -->|"composes"| node_sidebar
node_app -->|"composes"| node_chat_ui
node_app -->|"applies"| node_styles
node_app -->|"composes"| node_comparison_chat

node_dashboard --->|"loads analytics"| node_github_service
node_github_service --->|"normalizes data"| node_github_models
node_chat_service --->|"uses message schemas"| node_chat_models

node_chat_ui --->|"sends prompts"| node_chat_service
node_sidebar --->|"updates target and focus"| node_session
node_chat_ui --->|"renders history and logs"| node_session
node_app --->|"initializes"| node_session
node_chat_service -->|"uses context and records results"| node_session

node_session ~~~ node_config
node_chat_models ~~~ node_openai_service

node_config -->|"provides API settings"| node_openai_service
node_config -->|"provides token and command"| node_mcp_service

node_chat_service --->|"streams model turns"| node_openai_service
node_chat_service --->|"executes requested tools"| node_mcp_service
node_github_service --->|"requests GitHub tools"| node_mcp_service

node_openai_service -->|"Responses API"| node_openai_api
node_mcp_service -->|"JSON-RPC over stdio"| node_mcp_server
node_mcp_server -->|"GitHub tool access"| node_github_api
node_mcp_service -.->|"REST fallback"| node_github_api

click node_app "https://github.com/arcaneleague18/github-stalker-pro/blob/main/app.py"
click node_sidebar "https://github.com/arcaneleague18/github-stalker-pro/blob/main/ui/sidebar.py"
click node_dashboard "https://github.com/arcaneleague18/github-stalker-pro/blob/main/ui/dashboard.py"
click node_chat_ui "https://github.com/arcaneleague18/github-stalker-pro/blob/main/ui/chat.py"
click node_comparison_ui "https://github.com/arcaneleague18/github-stalker-pro/blob/main/ui/comparison.py"
click node_comparison_chat "https://github.com/arcaneleague18/github-stalker-pro/blob/main/ui/comparison_chat.py"
click node_styles "https://github.com/arcaneleague18/github-stalker-pro/blob/main/assets/styles.css"
click node_session "https://github.com/arcaneleague18/github-stalker-pro/blob/main/services/session_service.py"
click node_github_service "https://github.com/arcaneleague18/github-stalker-pro/blob/main/services/github_service.py"
click node_chat_service "https://github.com/arcaneleague18/github-stalker-pro/blob/main/services/chat_service.py"
click node_github_models "https://github.com/arcaneleague18/github-stalker-pro/blob/main/models/github_models.py"
click node_chat_models "https://github.com/arcaneleague18/github-stalker-pro/blob/main/models/chat_models.py"
click node_config "https://github.com/arcaneleague18/github-stalker-pro/blob/main/config.py"
click node_openai_service "https://github.com/arcaneleague18/github-stalker-pro/blob/main/services/openai_service.py"
click node_mcp_service "https://github.com/arcaneleague18/github-stalker-pro/blob/main/services/mcp_service.py"

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337

class node_app,node_sidebar,node_dashboard,node_chat_ui,node_comparison_ui,node_comparison_chat,node_styles toneBlue
class node_session,node_github_service,node_chat_service toneAmber
class node_github_models,node_chat_models toneMint
class node_config,node_openai_service,node_mcp_service,node_mcp_server,node_github_api,node_openai_api toneRose
```

### Architectural Principles
- **No Backend REST API:** Streamlit directly imports modular backend Python services.
- **No FastAPI / Flask:** Pure Python architecture optimized for Streamlit state management.
- **No Embeddings / FAISS / ChromaDB:** 100% dynamic Model Context Protocol execution.

---

## 🚀 Installation & Setup

> [!IMPORTANT]
> Ensure you have **Python 3.12+** installed on your system.

### 1. Clone & Navigate
```bash
git clone https://github.com/your-username/github-stalker-pro.git
cd github-stalker-pro
```

### 2. Install Dependencies
As per project rules, install the required packages yourself in your virtual environment:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the template file to `.env`:
```bash
cp .env.example .env
```
Open `.env` in your editor and configure your secrets:
```ini
# LLM API Configuration (Local Model Proxy)
OPENAI_BASE_URL="http://localhost:4000/openai/v1"
OPENAI_MODEL="vscode-lm-proxy"

# GitHub Personal Access Token (Required for MCP & API access)
# Create a token with 'repo', 'read:user', and 'read:org' scopes at https://github.com/settings/tokens
GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# MCP Server Command (Optional - defaults to Node npx)
MCP_SERVER_COMMAND="npx -y @modelcontextprotocol/server-github"
```

---

## 💻 Running Locally

Once your environment variables are configured and dependencies are installed, launch the Streamlit application:

```bash
streamlit run app.py
```

The application will automatically open in your default browser at `http://localhost:8501`.

---

## 🔌 Connecting to the GitHub MCP Server

The application communicates with the GitHub MCP server in two ways:

1. **Stdio Mode (Primary):** When you run the app, `services/mcp_service.py` launches `npx -y @modelcontextprotocol/server-github` as a child process using Python's `subprocess` module. It communicates using standard **JSON-RPC 2.0 over stdin/stdout**.
2. **HTTP REST Adapter Mode (Fallback):** If Node.js is not installed or the stdio process cannot be launched, the client seamlessly switches to an internal HTTP REST adapter that implements the exact same MCP tool schemas over standard GitHub API endpoints.

### Available MCP Tools
- `get_user`: Fetch profile details for any GitHub user.
- `list_user_repositories` / `search_repositories`: Discover public repositories.
- `get_repository`: Inspect repository metadata and branch details.
- `get_file_contents`: Read file contents, source code, and READMEs.
- `get_repository_tree`: Explore directory and file structures (with automatic branch fallback).
- `list_commits`: Check recent commit history.
- `list_branches` / `list_pull_requests` / `list_issues`: Review repository activity.
- `search_issues`: Search issues and pull requests across GitHub with advanced queries.
- `get_user_contributions`: Calculate total commits, issues, and PR contributions for timeframes.
- `list_user_followers` / `list_user_following`: Inspect social connections.
- `list_releases` / `list_tags` / `list_user_organizations`: Access extended metadata.

---

## 📂 Project Structure

```text
github-stalker-pro/
│
├── app.py                   # Streamlit main application entry point
├── config.py                # Environment management & Pydantic settings
├── requirements.txt         # Production Python dependencies
├── README.md                # Complete project documentation
├── .env.example             # Environment variable template
├── test_app.py              # Verification & mock testing script
│
├── services/                # Modular backend service layer
│   ├── __init__.py
│   ├── openai_service.py    # OpenAI Responses API & tool streaming client
│   ├── mcp_service.py       # Low-level Model Context Protocol (stdio/REST) client
│   ├── github_service.py    # High-level domain aggregation & in-memory caching
│   ├── chat_service.py      # Multi-turn chat orchestration & prompt injection
│   └── session_service.py   # Type-safe Streamlit session state manager
│
├── ui/                      # Streamlit frontend views and components
│   ├── __init__.py
│   ├── sidebar.py           # Sidebar navigation, user target & controls
│   ├── dashboard.py         # Visual metrics, profile card & language charts
│   └── chat.py              # ChatGPT interface, streaming & tool inspection
│
├── models/                  # Pydantic data modeling schemas
│   ├── __init__.py
│   ├── github_models.py     # GitHub User, Repository, Stats & Activity schemas
│   └── chat_models.py       # Chat messages, MCP tool schemas & session logs
│
├── utils/                   # Shared utility functions and logging
│   ├── __init__.py
│   ├── logger.py            # Colored ANSI console logger setup
│   └── helpers.py           # Formatting, error handling & language colors
│
└── assets/                  # Frontend styling & assets
    └── styles.css           # Premium dark theme glassmorphism stylesheet
```

---

## ❓ Troubleshooting

### 1. "Configuration Notice: OPENAI_API_KEY is missing"
- **Solution:** Ensure you created the `.env` file in the root directory and added your valid `OPENAI_API_KEY`. Check that `python-dotenv` is installed.

### 2. "MCP Server: Offline" or API Rate Limits
- **Solution:** Without a `GITHUB_PERSONAL_ACCESS_TOKEN`, GitHub limits unauthenticated requests to 60 per hour. Generate a token at [GitHub Developer Settings](https://github.com/settings/tokens) and paste it into your `.env` file.

### 3. Node.js / NPX Not Found Error in Logs
- **Solution:** This is normal if Node.js is not installed! The application will log a warning and automatically activate the high-resilience **HTTP REST Adapter Mode**, ensuring full functionality without requiring Node.js.

### 4. OpenAI Tool Calling Error or Model Not Found
- **Solution:** If you do not have access to `gpt-5.5` or specific preview models yet, the application will automatically catch the error and fallback to `gpt-4o`. You can also manually set `OPENAI_MODEL="gpt-4o"` in `.env`.

---

## 🔮 Future Improvements

- **Multi-Account Comparison:** Allow selecting two GitHub users side-by-side to compare repository activity, language preferences, and star growth.
- **Graph Visualization:** Render interactive D3.js / Mermaid dependency trees and contributor network graphs directly in Streamlit cards.
- **Export Analytics Report:** Add a button to generate and download a comprehensive PDF or Markdown executive summary of the developer's profile and repositories.
- **Docker MCP Support:** Provide a pre-built `docker-compose.yml` for isolated containerized MCP server execution.

---

## 📄 License

This project is open-source and developed as an advanced AI engineering demonstration of the **Model Context Protocol (MCP)**.

