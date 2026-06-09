import pytest
from unittest.mock import AsyncMock, MagicMock

import mcp_web_search.tools.web_search as web_search_tool
from mcp_web_search.tools.web_search import web_search


@pytest.fixture(autouse=True)
def setup_slots():
    # Store original values of slots
    orig_web_service = web_search_tool.web_service
    orig_metrics = web_search_tool.metrics
    orig_bg_writer = web_search_tool.background_writer

    yield

    # Restore original values of slots
    web_search_tool.web_service = orig_web_service
    web_search_tool.metrics = orig_metrics
    web_search_tool.background_writer = orig_bg_writer


@pytest.mark.asyncio
async def test_web_search_enqueues_background_task_on_success():
    # Arrange
    mock_web_service = AsyncMock()
    mock_web_service.search.return_value = "This is a successful search answer"
    web_search_tool.web_service = mock_web_service

    mock_bg_writer = MagicMock()
    web_search_tool.background_writer = mock_bg_writer

    # Act
    result = await web_search(
        query="how to use FastMCP",
        framework_name="fastmcp",
        framework_version="2.0"
    )

    # Assert
    assert result == "This is a successful search answer"
    mock_web_service.search.assert_awaited_once_with(
        query="how to use FastMCP",
        framework_name="fastmcp",
        framework_version="2.0"
    )
    mock_bg_writer.enqueue.assert_called_once_with(
        raw_query="how to use FastMCP",
        framework_name="fastmcp",
        framework_version="2.0",
        answer="This is a successful search answer"
    )


@pytest.mark.asyncio
async def test_web_search_skips_enqueue_on_mcp_error():
    # Arrange
    mock_web_service = AsyncMock()
    mock_web_service.search.return_value = "[MCP Error: Live web search currently unavailable]"
    web_search_tool.web_service = mock_web_service

    mock_bg_writer = MagicMock()
    web_search_tool.background_writer = mock_bg_writer

    # Act
    result = await web_search(
        query="how to use FastMCP",
        framework_name="fastmcp",
        framework_version="2.0"
    )

    # Assert
    assert result == "[MCP Error: Live web search currently unavailable]"
    mock_web_service.search.assert_awaited_once()
    mock_bg_writer.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_web_search_no_bg_writer():
    # Arrange
    mock_web_service = AsyncMock()
    mock_web_service.search.return_value = "Success without writer"
    web_search_tool.web_service = mock_web_service
    web_search_tool.background_writer = None

    # Act
    result = await web_search(
        query="how to use FastMCP",
        framework_name="fastmcp",
        framework_version="2.0"
    )

    # Assert
    assert result == "Success without writer"
    mock_web_service.search.assert_awaited_once()
