# Claude Agentic Flow

This repository contains an autonomous agentic pipeline framework designed for the Claude Code CLI. It consists of two main subprojects:

1. **`agentic-flow`**: The core template and framework configuration for the agentic flow.
2. **`web-search-mcp`**: A mandatory Model Context Protocol (MCP) tool required for the flow to operate correctly.

## ⚠️ Important: How to Use

**Everything inside the `agentic-flow` folder must be copied to the root directory of the target project where you want to use the agentic flow.** 

The `agentic-flow` folder contains essential framework rules, agent memory protocols, orchestration settings, and the `.claude` directory which defines the pipeline architecture, schemas, and skills.

## Subprojects Overview

### 1. Agentic Flow Template (`agentic-flow/`)
This is the framework template for Claude Code (`claude.ai/code`). It provides:
- **Framework Rules (`CLAUDE.md`)**: Contains critical instructions for agents, error resolution protocols, and memory management rules.
- **Orchestration (`.claude/`)**: Houses the orchestration logic, agent definitions, communication protocols (`PROTOCOL.md`), and skills necessary to run the full autonomous pipeline (architecture → planning → implementation → review → commit).

For more detailed documentation regarding the orchestration pipeline, please refer to [agentic-flow/.claude/README.md](agentic-flow/.claude/README.md).

To adopt this framework in a new project:
- If the project does not have Claude Code configured, simply copy the contents of `agentic-flow/` to your project and update the "Project-Specific Settings" section in `CLAUDE.md`.
- **If the target project already has a `.claude` folder and a `CLAUDE.md` file**, you must merge them carefully:
  - Join the existing `CLAUDE.md` file with the one from this project.
  - Merge the contents of the `.claude/` directory (check that the agents and skills do not have conflicting namings).
  - Join the `.claude/settings.json` from this project with the existing `settings.json`.

### 2. Web Search MCP Server (`web-search-mcp/`)
This is a mandatory MCP tool required by the agentic flow's error resolution and research protocols. It provides:
- **Web Search (`web_search`)**: Access to high-quality internet search results using Tavily.
- **Local Vector Cache (`db_search`)**: Intelligent caching of search results using ChromaDB and OpenAI embeddings to prevent redundant API calls.

**Setup Instructions for the MCP Tool:**
1. Navigate to the `web-search-mcp` directory.
2. Install dependencies using `uv` (`uv sync`) or `pip` (`pip install -e .`).
3. Copy `.env.example` to `.env` and configure your `TAVILY_API_KEY` and `OPENAI_API_KEY`.
4. Run the server using `uv run python -m mcp_web_search`.

For more details, refer to the [web-search-mcp/README.md](file:///C:/MyProjects/AI/claude-agentic-flow/web-search-mcp/README.md).
