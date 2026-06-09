import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
import pytest

from mcp_web_search.services.background import BackgroundWriter, _BACKGROUND_TASKS


@pytest.mark.asyncio
async def test_background_writer_success():
    # Arrange
    mock_summarizer = AsyncMock()
    mock_summarizer.simplify.return_value = "simplified query"

    mock_embedder = AsyncMock()
    mock_embedder.embed_async.return_value = [[0.1, 0.2, 0.3]]

    mock_cache_service = AsyncMock()

    writer = BackgroundWriter(
        summarizer=mock_summarizer,
        embedder=mock_embedder,
        cache_service=mock_cache_service
    )

    # Act
    writer.enqueue(
        raw_query="some long raw query",
        framework_name="test-framework",
        framework_version="1.0.0",
        answer="the final answer"
    )

    # Allow the event loop to run tasks
    await asyncio.sleep(0.1)

    # Assert
    mock_summarizer.simplify.assert_awaited_once_with("some long raw query")
    mock_embedder.embed_async.assert_awaited_once_with(["simplified query"])
    mock_cache_service.upsert.assert_awaited_once_with(
        simplified_query="simplified query",
        framework_name="test-framework",
        framework_version="1.0.0",
        answer="the final answer",
        embedding=[0.1, 0.2, 0.3]
    )
    # Ensure task was removed from the set
    assert len(_BACKGROUND_TASKS) == 0


@pytest.mark.asyncio
async def test_background_writer_exception_in_summarize(caplog):
    # Arrange
    mock_summarizer = AsyncMock()
    mock_summarizer.simplify.side_effect = ValueError("LLM failure")

    mock_embedder = AsyncMock()
    mock_cache_service = AsyncMock()

    writer = BackgroundWriter(
        summarizer=mock_summarizer,
        embedder=mock_embedder,
        cache_service=mock_cache_service
    )

    # Act
    with caplog.at_level(logging.WARNING):
        writer.enqueue(
            raw_query="some long raw query",
            framework_name="test-framework",
            framework_version="1.0.0",
            answer="the final answer"
        )
        await asyncio.sleep(0.1)

    # Assert
    mock_summarizer.simplify.assert_awaited_once()
    mock_embedder.embed_async.assert_not_awaited()
    mock_cache_service.upsert.assert_not_awaited()

    assert len(_BACKGROUND_TASKS) == 0
    # Verify that the failure was logged at WARN/WARNING
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "Background caching pipeline failed" in warnings[0].message
    assert "LLM failure" in warnings[0].message


@pytest.mark.asyncio
async def test_background_writer_exception_in_embedder(caplog):
    # Arrange
    mock_summarizer = AsyncMock()
    mock_summarizer.simplify.return_value = "simplified query"

    mock_embedder = AsyncMock()
    mock_embedder.embed_async.side_effect = RuntimeError("Embedding API down")

    mock_cache_service = AsyncMock()

    writer = BackgroundWriter(
        summarizer=mock_summarizer,
        embedder=mock_embedder,
        cache_service=mock_cache_service
    )

    # Act
    with caplog.at_level(logging.WARNING):
        writer.enqueue(
            raw_query="some long raw query",
            framework_name="test-framework",
            framework_version="1.0.0",
            answer="the final answer"
        )
        await asyncio.sleep(0.1)

    # Assert
    mock_summarizer.simplify.assert_awaited_once()
    mock_embedder.embed_async.assert_awaited_once_with(["simplified query"])
    mock_cache_service.upsert.assert_not_awaited()

    assert len(_BACKGROUND_TASKS) == 0
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "Background caching pipeline failed" in warnings[0].message
    assert "Embedding API down" in warnings[0].message


@pytest.mark.asyncio
async def test_background_writer_empty_embeddings(caplog):
    # Arrange
    mock_summarizer = AsyncMock()
    mock_summarizer.simplify.return_value = "simplified query"

    mock_embedder = AsyncMock()
    mock_embedder.embed_async.return_value = []  # Empty embeddings

    mock_cache_service = AsyncMock()

    writer = BackgroundWriter(
        summarizer=mock_summarizer,
        embedder=mock_embedder,
        cache_service=mock_cache_service
    )

    # Act
    with caplog.at_level(logging.WARNING):
        writer.enqueue(
            raw_query="some long raw query",
            framework_name="test-framework",
            framework_version="1.0.0",
            answer="the final answer"
        )
        await asyncio.sleep(0.1)

    # Assert
    mock_summarizer.simplify.assert_awaited_once()
    mock_embedder.embed_async.assert_awaited_once_with(["simplified query"])
    mock_cache_service.upsert.assert_not_awaited()

    assert len(_BACKGROUND_TASKS) == 0
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "Background caching pipeline failed" in warnings[0].message
    assert "Embedder returned empty embeddings" in warnings[0].message


@pytest.mark.asyncio
async def test_background_writer_exception_in_cache(caplog):
    # Arrange
    mock_summarizer = AsyncMock()
    mock_summarizer.simplify.return_value = "simplified query"

    mock_embedder = AsyncMock()
    mock_embedder.embed_async.return_value = [[0.1, 0.2, 0.3]]

    mock_cache_service = AsyncMock()
    mock_cache_service.upsert.side_effect = Exception("Chroma write error")

    writer = BackgroundWriter(
        summarizer=mock_summarizer,
        embedder=mock_embedder,
        cache_service=mock_cache_service
    )

    # Act
    with caplog.at_level(logging.WARNING):
        writer.enqueue(
            raw_query="some long raw query",
            framework_name="test-framework",
            framework_version="1.0.0",
            answer="the final answer"
        )
        await asyncio.sleep(0.1)

    # Assert
    mock_summarizer.simplify.assert_awaited_once()
    mock_embedder.embed_async.assert_awaited_once()
    mock_cache_service.upsert.assert_awaited_once()

    assert len(_BACKGROUND_TASKS) == 0
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "Background caching pipeline failed" in warnings[0].message
    assert "Chroma write error" in warnings[0].message


@pytest.mark.asyncio
async def test_background_writer_timing_and_task_reference():
    import time

    # Arrange
    # A fake summarizer that sleeps for 200ms
    async def fake_simplify(query):
        await asyncio.sleep(0.2)
        return "simplified query"

    mock_summarizer = MagicMock()
    mock_summarizer.simplify = fake_simplify

    mock_embedder = AsyncMock()
    mock_embedder.embed_async.return_value = [[0.1, 0.2, 0.3]]

    mock_cache_service = AsyncMock()

    writer = BackgroundWriter(
        summarizer=mock_summarizer,
        embedder=mock_embedder,
        cache_service=mock_cache_service
    )

    # Act: Measure enqueue duration
    start_time = time.perf_counter()
    writer.enqueue(
        raw_query="some long raw query",
        framework_name="test-framework",
        framework_version="1.0.0",
        answer="the final answer"
    )
    duration = time.perf_counter() - start_time

    # Assert enqueue returns immediately (<10ms)
    assert duration < 0.01, f"enqueue blocked for {duration} seconds"

    # Assert cache.upsert has NOT been called yet
    mock_cache_service.upsert.assert_not_awaited()

    # Assert task reference is held in the module-level set during execution
    assert len(_BACKGROUND_TASKS) == 1
    task = list(_BACKGROUND_TASKS)[0]
    assert not task.done()

    # Now let the event loop run and complete the task
    await asyncio.sleep(0.3)

    # Assert task is now completed, cache.upsert has been called, and task is removed from set
    assert task.done()
    mock_cache_service.upsert.assert_awaited_once()
    assert len(_BACKGROUND_TASKS) == 0

