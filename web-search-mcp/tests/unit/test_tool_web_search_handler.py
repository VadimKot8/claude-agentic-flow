"""Unit tests for the web_search tool handler."""

import pytest
from unittest.mock import AsyncMock, patch
import mcp_web_search.tools.web_search as web_search_module


@pytest.mark.asyncio
async def test_web_search_handler_delegates_to_web_service() -> None:
    # Arrange
    mock_web_service = AsyncMock()
    mock_web_service.search.return_value = "Search result from service"
    
    mock_metrics = AsyncMock()

    # Inject mock dependencies
    web_search_module.web_service = mock_web_service
    web_search_module.metrics = mock_metrics

    try:
        # Act
        result = await web_search_module.web_search(
            query="how to run tests",
            framework_name="pytest",
            framework_version="8.0.0",
        )

        # Assert
        assert result == "Search result from service"
        mock_metrics.increment_web_search.assert_called_once()
        mock_web_service.search.assert_called_once_with(
            query="how to run tests",
            framework_name="pytest",
            framework_version="8.0.0",
        )
    finally:
        # Clean up global state
        web_search_module.web_service = None
        web_search_module.metrics = None


@pytest.mark.asyncio
async def test_web_search_handler_handles_missing_web_service() -> None:
    # Arrange
    mock_metrics = AsyncMock()
    web_search_module.web_service = None
    web_search_module.metrics = mock_metrics

    try:
        # Act
        result = await web_search_module.web_search(
            query="how to run tests",
            framework_name="pytest",
            framework_version="8.0.0",
        )

        # Assert
        assert (
            result
            == "[MCP Error: Live web search currently unavailable. Overreaching fallback active.]"
        )
        mock_metrics.increment_web_search.assert_not_called()
    finally:
        # Clean up global state
        web_search_module.metrics = None

