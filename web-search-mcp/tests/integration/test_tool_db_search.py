import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastmcp import Client
from mcp_web_search.config import Config
from mcp_web_search.server import mcp
from mcp_web_search.llm.base import ChatLLM, Embeddings
from mcp_web_search.services.summarizer import Summarizer
from mcp_web_search.services.embedder import ChromaEmbedder
from mcp_web_search.services.cache import CacheService
from mcp_web_search.services.background import BackgroundWriter, _BACKGROUND_TASKS
from mcp_web_search.services.web import WebService

import mcp_web_search.tools.web_search as web_search_tool
import mcp_web_search.tools.db_search as db_search_tool


@pytest.fixture
def setup_integration_env(tmp_path):
    # Store original slot values
    orig_web_service = web_search_tool.web_service
    orig_metrics = web_search_tool.metrics
    orig_bg_writer = web_search_tool.background_writer
    orig_embedder = db_search_tool.embedder
    orig_cache = db_search_tool.cache_service
    orig_summarizer = db_search_tool.summarizer

    # Create dummy config with temp path for Chroma
    config = Config(
        TAVILY_API_KEY="dummy-tavily-key",
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="dummy-openai-key",
        EMBEDDING_MODEL="text-embedding-3-small",
        SUMMARIZATION_MODEL="gpt-4o-mini",
        CHROMA_PATH=str(tmp_path),
        CHROMA_COLLECTION="integration_test_collection",
        CACHE_TTL_DAYS=30,
        SIMILARITY_THRESHOLD=0.85,
        TAVILY_COST_PER_SEARCH_USD=0.015,
        TAVILY_FREE_TIER_ALLOCATION=1000,
        MCP_HTTP_HOST="127.0.0.1",
        MCP_HTTP_PORT=8765
    )

    # Mock LLM and Embeddings
    mock_llm = AsyncMock(spec=ChatLLM)
    mock_llm.complete.return_value = "simplified query"

    mock_embeddings = AsyncMock(spec=Embeddings)
    # Return a 1536-dimensional mock embedding (matching text-embedding-3-small default)
    mock_embedding_vector = [0.1] * 1536
    mock_embeddings.embed.return_value = [mock_embedding_vector]

    # Instantiate services
    summarizer = Summarizer(llm=mock_llm)
    embedder = ChromaEmbedder(embedder=mock_embeddings)
    cache_service = CacheService(config=config, embedder=embedder)
    background_writer = BackgroundWriter(
        summarizer=summarizer,
        embedder=embedder,
        cache_service=cache_service
    )
    web_service = WebService(config)

    # Wire services to tool slots
    web_search_tool.web_service = web_service
    web_search_tool.metrics = None
    web_search_tool.background_writer = background_writer
    db_search_tool.embedder = embedder
    db_search_tool.cache_service = cache_service
    db_search_tool.summarizer = summarizer

    # Ensure collection is clean
    yield

    # Clean up and restore slots
    web_search_tool.web_service = orig_web_service
    web_search_tool.metrics = orig_metrics
    web_search_tool.background_writer = orig_bg_writer
    db_search_tool.embedder = orig_embedder
    db_search_tool.cache_service = orig_cache
    db_search_tool.summarizer = orig_summarizer


@pytest.mark.asyncio
async def test_integration_db_search_cache_hit_and_miss(setup_integration_env):
    """Test that seeding via web_search results in a db_search hit for the same version and a miss for another."""
    with patch("mcp_web_search.services.web.TavilyClient") as mock_tavily_class:
        mock_tavily_client = MagicMock()
        mock_tavily_class.return_value = mock_tavily_client
        mock_tavily_client.search.return_value = {
            "answer": "This is the fresh answer from Tavily"
        }

        async with Client(mcp) as client:
            # 1. Call web_search to fetch the answer and spawn background caching
            web_response = await client.call_tool(
                "web_search",
                arguments={
                    "query": "how to build langchain agents",
                    "framework_name": "langchain",
                    "framework_version": "0.3.1"
                }
            )
            assert web_response.content[0].text == "This is the fresh answer from Tavily"

            # 2. Wait for the background caching task to complete
            if _BACKGROUND_TASKS:
                await asyncio.gather(*list(_BACKGROUND_TASKS), return_exceptions=True)

            # 3. Call db_search with the exact same framework name and version (should hit cache)
            db_response = await client.call_tool(
                "db_search",
                arguments={
                    "query": "how to build langchain agents",
                    "framework_name": "langchain",
                    "framework_version": "0.3.1"
                }
            )
            
            # The result is returned as a text content containing a JSON or dict
            import json
            result_data = json.loads(db_response.content[0].text)
            assert result_data["status"] == "success"
            assert result_data["answer"] == "This is the fresh answer from Tavily"
            assert "similarity_score" in result_data
            assert "timestamp" in result_data

            # 4. Call db_search with a different framework version (should miss cache)
            db_response_miss = await client.call_tool(
                "db_search",
                arguments={
                    "query": "how to build langchain agents",
                    "framework_name": "langchain",
                    "framework_version": "0.3.2"  # Mismatched version
                }
            )
            result_data_miss = json.loads(db_response_miss.content[0].text)
            assert result_data_miss["status"] == "cache_miss"
