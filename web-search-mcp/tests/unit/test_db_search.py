import logging
from unittest.mock import AsyncMock
import pytest

from mcp_web_search.services.cache import CacheHit
import mcp_web_search.tools.db_search as db_search_tool
from mcp_web_search.tools.db_search import db_search


@pytest.fixture(autouse=True)
def setup_dependencies():
    # Store original values
    orig_embedder = db_search_tool.embedder
    orig_cache = db_search_tool.cache_service
    orig_summarizer = db_search_tool.summarizer

    # Default to no summarizer unless a test opts in.
    db_search_tool.summarizer = None

    yield

    # Restore original values
    db_search_tool.embedder = orig_embedder
    db_search_tool.cache_service = orig_cache
    db_search_tool.summarizer = orig_summarizer


@pytest.mark.asyncio
async def test_db_search_success():
    # Arrange
    mock_embedder = AsyncMock()
    mock_embedder.embed_async.return_value = [[0.1, 0.2, 0.3]]

    mock_cache_service = AsyncMock()
    mock_cache_service.query.return_value = CacheHit(
        answer="cached answer",
        timestamp=123456789,
        similarity_score=0.95
    )

    db_search_tool.embedder = mock_embedder
    db_search_tool.cache_service = mock_cache_service

    # Act
    result = await db_search(
        query="test query",
        framework_name="test-framework",
        framework_version="1.0.0"
    )

    # Assert
    assert result == {
        "status": "success",
        "answer": "cached answer",
        "timestamp": 123456789,
        "similarity_score": 0.95
    }
    mock_embedder.embed_async.assert_awaited_once_with(["test query"])
    mock_cache_service.query.assert_awaited_once_with(
        embedded_query=[0.1, 0.2, 0.3],
        framework_name="test-framework",
        framework_version="1.0.0"
    )


@pytest.mark.asyncio
async def test_db_search_simplifies_query_before_embedding():
    # Arrange: a summarizer is injected, so the raw query should be simplified
    # to the canonical phrase before embedding (read/write symmetry).
    mock_summarizer = AsyncMock()
    mock_summarizer.simplify.return_value = "instantiate agent"

    mock_embedder = AsyncMock()
    mock_embedder.embed_async.return_value = [[0.1, 0.2, 0.3]]

    mock_cache_service = AsyncMock()
    mock_cache_service.query.return_value = CacheHit(
        answer="cached answer",
        timestamp=123456789,
        similarity_score=0.95,
    )

    db_search_tool.summarizer = mock_summarizer
    db_search_tool.embedder = mock_embedder
    db_search_tool.cache_service = mock_cache_service

    # Act
    result = await db_search(
        query="How do I instantiate an agent?? please help!!",
        framework_name="langchain",
        framework_version="0.3.1",
    )

    # Assert: the simplified phrase (not the raw query) was embedded.
    assert result["status"] == "success"
    mock_summarizer.simplify.assert_awaited_once_with(
        "How do I instantiate an agent?? please help!!"
    )
    mock_embedder.embed_async.assert_awaited_once_with(["instantiate agent"])


@pytest.mark.asyncio
async def test_db_search_falls_back_to_raw_query_when_summarization_fails(caplog):
    # Arrange: summarizer raises; db_search must still query using the raw query.
    mock_summarizer = AsyncMock()
    mock_summarizer.simplify.side_effect = Exception("LLM down")

    mock_embedder = AsyncMock()
    mock_embedder.embed_async.return_value = [[0.1, 0.2, 0.3]]

    mock_cache_service = AsyncMock()
    mock_cache_service.query.return_value = None

    db_search_tool.summarizer = mock_summarizer
    db_search_tool.embedder = mock_embedder
    db_search_tool.cache_service = mock_cache_service

    # Act
    with caplog.at_level(logging.WARNING):
        result = await db_search(
            query="raw query text",
            framework_name="langchain",
            framework_version="0.3.1",
        )

    # Assert: degraded gracefully and embedded the raw query.
    assert result == {"status": "cache_miss"}
    mock_embedder.embed_async.assert_awaited_once_with(["raw query text"])
    assert any(
        "summarization failed" in r.message for r in caplog.records
    )


@pytest.mark.asyncio
async def test_db_search_cache_miss():
    # Arrange
    mock_embedder = AsyncMock()
    mock_embedder.embed_async.return_value = [[0.1, 0.2, 0.3]]

    mock_cache_service = AsyncMock()
    mock_cache_service.query.return_value = None

    db_search_tool.embedder = mock_embedder
    db_search_tool.cache_service = mock_cache_service

    # Act
    result = await db_search(
        query="test query",
        framework_name="test-framework",
        framework_version="1.0.0"
    )

    # Assert
    assert result == {"status": "cache_miss"}
    mock_embedder.embed_async.assert_awaited_once()
    mock_cache_service.query.assert_awaited_once()


@pytest.mark.asyncio
async def test_db_search_uninitialized_dependencies():
    # Arrange
    db_search_tool.embedder = None
    db_search_tool.cache_service = None

    # Act
    result = await db_search(
        query="test query",
        framework_name="test-framework",
        framework_version="1.0.0"
    )

    # Assert
    assert result == {"status": "cache_miss"}


@pytest.mark.asyncio
async def test_db_search_embed_failure(caplog):
    # Arrange
    mock_embedder = AsyncMock()
    mock_embedder.embed_async.side_effect = Exception("OpenAI API error")

    mock_cache_service = AsyncMock()

    db_search_tool.embedder = mock_embedder
    db_search_tool.cache_service = mock_cache_service

    # Act
    with caplog.at_level(logging.WARNING):
        result = await db_search(
            query="test query",
            framework_name="test-framework",
            framework_version="1.0.0"
        )

    # Assert
    assert result == {"status": "cache_miss"}
    mock_cache_service.query.assert_not_awaited()
    
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "Error during db_search cache retrieval" in warnings[0].message
    assert "OpenAI API error" in warnings[0].message


@pytest.mark.asyncio
async def test_db_search_cache_query_failure(caplog):
    # Arrange
    mock_embedder = AsyncMock()
    mock_embedder.embed_async.return_value = [[0.1, 0.2, 0.3]]

    mock_cache_service = AsyncMock()
    mock_cache_service.query.side_effect = Exception("Chroma connection error")

    db_search_tool.embedder = mock_embedder
    db_search_tool.cache_service = mock_cache_service

    # Act
    with caplog.at_level(logging.WARNING):
        result = await db_search(
            query="test query",
            framework_name="test-framework",
            framework_version="1.0.0"
        )

    # Assert
    assert result == {"status": "cache_miss"}
    
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "Error during db_search cache retrieval" in warnings[0].message
    assert "Chroma connection error" in warnings[0].message
