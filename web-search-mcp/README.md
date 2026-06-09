# MCP Web Search Server

An MCP (Model Context Protocol) server providing web search capabilities with intelligent local vector caching using Tavily and ChromaDB. It exposes an interface for querying search and maintaining a local context to prevent redundant external API calls and accelerate repeated or similar questions.

## Features

- **Tavily Web Search**: Access to high-quality internet search results optimized for LLM consumption via the `web_search` tool.
- **Local Vector Cache**: Uses ChromaDB to locally persist search results and vector embeddings for semantic retrieval via the `db_search` tool.
- **Query Summarization & Embedding**: Simplifies queries and computes semantic vector embeddings utilizing OpenAI models before storing them in ChromaDB.
- **Cache Invalidation & TTL**: Built-in mechanisms to evict stale caches based on a configurable time-to-live period.
- **Deterministic Deduplication**: Cache uses structural normalization (lowercase, stripping punctuation, and whitespace) along with framework name and version matching for high precision cache hit rates.

## Prerequisites

- **Python**: `>= 3.13`
- **Package Manager**: [uv](https://github.com/astral-sh/uv) or `hatchling` (as configured in `pyproject.toml`)

## Obligatory Environment Variables

To run the server normally, the following environment variables are **required**:

- `TAVILY_API_KEY` - Your API key for the Tavily web search service.
- `OPENAI_API_KEY` - Your API key for OpenAI, required when the `LLM_PROVIDER` is set to `openai` (which is the default).

*Note: You can copy `.env.example` to `.env` and fill in your keys. Other configuration options such as model selection, HTTP server bind address/port, and cache TTL have sensible defaults provided in `.env.example`.*

## How to Run

1. **Install dependencies**:
   Using `uv`:
   ```bash
   uv sync
   ```
   Or install standard dependencies into your virtual environment:
   ```bash
   pip install -e .
   ```

2. **Set up the environment**:
   Make sure you have your `.env` file configured in the project root:
   ```bash
   cp .env.example .env
   # Edit .env and supply TAVILY_API_KEY and OPENAI_API_KEY
   ```

3. **Start the MCP Server**:
   You can run the server directly via Python:
   ```bash
   python -m mcp_web_search
   ```
   Or using `uv`:
   ```bash
   uv run python -m mcp_web_search
   ```
   The server runs a FastMCP HTTP application on the default `127.0.0.1:8000` (can be altered via `MCP_HTTP_HOST` and `MCP_HTTP_PORT` in `.env`).

## Architecture Overview

The system runs as a single-process server exposing its tools over `streamable-http`. It separates retrieval into two paths:
- `db_search`: Evaluates local cache using strict vector similarity.
- `web_search`: Always hits the live web via Tavily and writes back to the local database in a non-blocking background task.

For deep details, see the architecture documentation under `.docs/mcp_tavily_chromadb_architecture.md`.
