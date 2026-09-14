# Changelog

All notable changes to the **GitHub Stalker Pro** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **AI Assistant Status Indicator**: Added live LLM connection monitor to the sidebar alongside the MCP Server indicator, showing real-time connectivity (`● Connected` / `● Offline`).
- **`search_issues` MCP Tool**: Added new MCP tool schema and GitHub Search REST handler to query issues and pull requests globally (`author:USERNAME type:issue`) without looping over repositories.
- **Export Intelligence Report**: Added one-click **"Download Intelligence Report (.md)"** button in the dashboard to generate and download a comprehensive Markdown report of the analyzed developer.
- **Dynamic Git Branch Fallback**: Automatically retries with `master` branch if fetching repository trees on the default `main` branch returns a 404 error.
- **Expanded Test Suite**: Added automated tests in `test_app.py` validating `format_number` edge cases, `search_issues` OpenAI schema conversion, and LLM proxy connectivity.

### Fixed
- **Input Instruction Overlay**: Removed clumsy Streamlit `"Press Enter to submit form"` / `"Press Enter to apply"` overlay text in sidebar text inputs via targeted CSS in `assets/styles.css`.
- **Number Formatting Bug**: Fixed string formatting logic in `utils/helpers.py` that produced duplicated unit suffixes (e.g., `1.5MM` instead of `1.5M`).
- **Unbound Variable in MCP Service**: Resolved `NameError: name 'FALLBACK_TOOLS' is not defined` when discovering stdio MCP tools in `services/mcp_service.py`.
- **Branding Consistency**: Harmonized naming to **GitHub Stalker Pro** across `sidebar.py`, `README.md`, and MCP client initialization metadata.

---

## [0.1.0] - 2026-09-10

### Added
- **Zero-RAG AI Architecture**: Dynamic GitHub inspection powered by Model Context Protocol (MCP) tool execution, eliminating vector databases and stale embeddings.
- **Dual-Mode MCP Client**: Primary stdio JSON-RPC 2.0 communication with automatic fallback to high-resilience HTTP REST adapter mode.
- **16 Core MCP Tools**: Support for inspecting users, repositories, READMEs, file trees, commit histories, branches, tags, releases, pull requests, issues, and contributions.
- **Followers & Social Graph Tools**: Added `list_user_followers` and `list_user_following` MCP tools.
- **Interactive Analytics Dashboard**:
  - Profile banner with followers, following, company, location, and website metadata.
  - Interactive Altair-powered programming language distribution bar charts and badges.
  - Top starred repository cards with star/fork counters and **"Focus in Chat"** context locking buttons.
  - Organization memberships and recent public activity timeline expanders.
- **Deep AI Conversation Interface**:
  - Real-time token streaming from OpenAI Responses API / local model proxy.
  - Expandable MCP Tool Execution logs displaying exact JSON arguments and tool outputs.
  - Interactive suggested prompts grid for instant architectural questions.
  - Pinned bottom viewport chat input with automatic sidebar collapse adjustment.
- **Local Model Proxy Integration**: Support for running against local proxies (e.g. `vscode-lm-proxy`) via `OPENAI_BASE_URL` and `OPENAI_MODEL`.
- **Design System & Styling**:
  - GitHub Primer-inspired dark theme with glassmorphism cards and glowing gradients.
  - Typography powered by Google Font **Outfit** and **JetBrains Mono**.
  - Crisp base64-encoded SVG icons (`utils/icons.py`).
- **In-Memory Caching**: Session-level metric caching to prevent GitHub API rate limiting.
- **Automated Verification**: Pydantic models, helper utilities, and service initialization tests in `test_app.py`.
