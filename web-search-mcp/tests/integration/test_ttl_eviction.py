import asyncio
import time
import json
import pytest
from unittest.mock import AsyncMock, patch

from fastmcp import Client
from mcp_web_search.config import Config
from mcp_web_search.server import mcp
from mcp_web_search.llm.base import ChatLLM, Embeddings
from mcp_web_search.services.summarizer import Summarizer
from mcp_web_search.services.embedder import ChromaEmbedder
from mcp_web_search.services.cache import CacheService
from mcp_web_search.services.background import BackgroundWriter
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

    # Create config with temp path for Chroma and 30-day CACHE_TTL_DAYS
    config = Config(
        TAVILY_API_KEY="dummy-tavily-key",
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="dummy-openai-key",
        EMBEDDING_MODEL="text-embedding-3-small",
        SUMMARIZATION_MODEL="gpt-4o-mini",
        CHROMA_PATH=str(tmp_path),
        CHROMA_COLLECTION="ttl_test_collection",
        CACHE_TTL_DAYS=30,
        SIMILARITY_THRESHOLD=0.85,
        TAVILY_COST_PER_SEARCH_USD=0.015,
        TAVILY_FREE_TIER_ALLOCATION=1000,
        MCP_HTTP_HOST="127.0.0.1",
        MCP_HTTP_PORT=8765
    )

    # Mock LLM and Embeddings
    mock_llm = AsyncMock(spec=ChatLLM)
    mock_llm.complete.return_value = "expired query"

    mock_embeddings = AsyncMock(spec=Embeddings)
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

    yield cache_service

    # Clean up and restore slots
    web_search_tool.web_service = orig_web_service
    web_search_tool.metrics = orig_metrics
    web_search_tool.background_writer = orig_bg_writer
    db_search_tool.embedder = orig_embedder
    db_search_tool.cache_service = orig_cache
    db_search_tool.summarizer = orig_summarizer


@pytest.mark.asyncio
async def test_integration_ttl_eviction(setup_integration_env):
    """Test that a record older than CACHE_TTL_DAYS causes a cache_miss and is physically deleted from Chroma."""
    cache_service = setup_integration_env

    # 1. Directly insert a record with a timestamp older than CACHE_TTL_DAYS (e.g. 31 days ago)
    current_time = time.time()
    expired_timestamp = current_time - (31 * 24 * 60 * 60)

    # Perform the insert under the old timestamp
    with patch("mcp_web_search.services.cache.time.time", return_value=expired_timestamp):
        await cache_service.upsert(
            simplified_query="expired query",
            framework_name="langchain",
            framework_version="0.3.1",
            answer="This answer is expired",
            embedding=[0.1] * 1536
        )

    # Verify that the record is in Chroma before query
    collection = await cache_service._get_collection()
    initial_records = collection.get()
    assert len(initial_records["ids"]) == 1

    # 2. Call db_search with current time (which should detect expiration, delete the record, and miss)
    async with Client(mcp) as client:
        db_response = await client.call_tool(
            "db_search",
            arguments={
                "query": "expired query",
                "framework_name": "langchain",
                "framework_version": "0.3.1"
            }
        )

        result_data = json.loads(db_response.content[0].text)
        assert result_data["status"] == "cache_miss"

    # 3. Assert that the record was physically deleted from Chroma
    post_query_records = collection.get()
    assert len(post_query_records["ids"]) == 0
