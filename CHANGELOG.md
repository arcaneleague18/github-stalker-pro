# Changelog

All notable changes to the **GitHub Stalker Pro** project are documented here chronologically by date.

## 2026-09-15

### Added
- **Dual-Developer Comparative AI Chat**:
  - Added dedicated `render_comparison_chat` in `ui/comparison_chat.py` integrated as a top-level tab (`💬 Dual-Developer AI Chat`) on the Developer Comparison page.
  - Implemented cross-developer comparative system prompt in `services/chat_service.py` (`build_comparison_system_prompt`) instructing the model on finding shared projects, mutual repository contributions, shared organizations, and comparing repository architectures via MCP tools.
  - Added quick comparative suggested questions ("Did they do any projects together?", "Are they part of any shared organization?", "What are their contributions in that organization?", "Do any of their repos have similar architecture?").
  - Isolated comparative session history in `services/session_service.py` (`compare_messages`, `add_compare_message`, `clear_compare_chat`) preventing cross-contamination with single-account chat.
  - Added sidebar controls in comparison mode allowing one-click clearing of comparative chat and resetting targets.
  - Added automated test coverage in `test_app.py` validating comparative system prompt generation and session isolation.
- **Developer Comparison Showdown (Separate Page)**:
  - Implemented Streamlit 1.36+ `st.navigation` multi-page routing with **👤 Account Inspector** and **⚔️ Compare Developers** tabs.
  - Added dedicated comparison interface in `ui/comparison.py` allowing any two GitHub developers to be compared side-by-side.
  - Side-by-side developer profile dossiers displaying avatars, bios, companies, locations, and follower/following metrics.
  - Head-to-Head scorecard with automatic `🏆 Leader` badges comparing stars, forks, public repositories, and follower counts.
  - Grouped Altair multi-language comparative bar chart displaying programming language breakdown for both developers.
  - Top 3 starred repository showdown showcasing primary projects, stars, forks, and language badges.
  - **AI Architectural Comparison**: Streams an LLM architectural breakdown analyzing engineering paradigms, core technology stacks, design philosophies, and open-source impact.
  - **Download Comparative Dossier (.md)**: One-click export downloading a formatted Markdown comparison document.
  - Added automated test coverage in `test_app.py` for comparison generator and module validation.
- **Direct Hero Search on Welcome Screen**:
  - Added a centered username search form directly on the main welcome screen so accounts can be analyzed immediately without having to use the sidebar.

### Changed & Fixed
- **Removed All Sample Usernames & Presets**:
  - Cleaned all hardcoded sample usernames, popular showdown preset chips, quick picks, and sample names from placeholders across the entire application and service layers.
- **Sidebar Usability & Scrolling Fix**:
  - Enabled smooth vertical scrolling (`overflow-y: auto !important`) on the sidebar container for smaller laptop viewports.
  - Compacted sidebar header, combined MCP and AI Assistant indicators into a unified status card, and collapsed input labels so the account input field stays comfortably in view.

---

## 2026-09-14

### Added
- **AI Assistant Status Indicator**: Added a live LLM connection monitor to the sidebar alongside the MCP Server indicator, showing real-time connectivity (`● Connected` / `● Offline`).
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

## 2026-09-10

### Added
- **Followers & Social Graph Tools**: Added `list_user_followers` and `list_user_following` MCP tools.

### Fixed
- **Chat Input Box**: Fixed fixed-bottom chat input container styling and responsive alignment with sidebar collapse states.

---

## 2026-09-09

### Fixed
- **Location Rendering**: Fixed profile location display formatting on developer profile cards.

### Changed
- **Icon System Overhaul**: Replaced emojis across the interface with crisp inline base64 SVG icons (`utils/icons.py`) for a more consistent, professional design.

---

## 2026-09-06

### Changed
- **Local Model Proxy Setup**: Removed OpenRouter configuration and switched to local model proxy configuration (`http://localhost:4000/openai/v1`, `vscode-lm-proxy`).

---

## 2026-07-28

### Added
- **Initial Project Architecture**: Initialized GitHub Stalker Pro with Streamlit, local model proxy client, and Model Context Protocol (MCP) integration.
- **Zero-RAG Design**: Real-time queries directly against GitHub's live APIs via MCP tool calling without vector databases or embedding pipelines.
- **Dual-Mode MCP Client**: Stdio JSON-RPC 2.0 communication with automatic fallback to an internal HTTP REST adapter.
- **Core MCP Tooling**: Initial suite of MCP tools for inspecting users, repositories, README files, file trees, commit histories, branches, tags, releases, pull requests, issues, and contributions.
- **Interactive Analytics Dashboard**:
  - Profile banner with followers, following, company, location, and website links.
  - Interactive Altair-powered programming language distribution bar charts and badges.
  - Top starred repository cards with star/fork statistics and **"Focus in Chat"** context locking buttons.
  - Expandable panels for affiliated organizations and recent public activity events.
- **Deep AI Conversation Interface**:
  - Real-time response streaming from OpenAI Responses API / local model proxy.
  - Expandable MCP Tool Execution logs displaying exact JSON arguments and tool outputs.
  - Interactive suggested prompts grid for instant architectural questions.
- **In-Memory Caching**: Session-level caching for profile metrics to avoid GitHub API rate limiting.
- **Testing & Verification**: Initial test harness in `test_app.py` for models, helpers, and service initialization.
