"""Unit tests for the WebService class."""

import pytest
from unittest.mock import MagicMock, patch
from mcp_web_search.services.web import WebService
from mcp_web_search.config import Config


@pytest.mark.asyncio
async def test_web_service_search_happy_path() -> None:
    # Arrange
    api_key = "test-tavily-key"
    query = "test query"
    framework_name = "test-framework"
    framework_version = "1.0.0"
    expected_answer = "This is a search result."

    # Set up mock client and response
    with patch("mcp_web_search.services.web.TavilyClient") as mock_tavily_class:
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = {"answer": expected_answer, "results": []}

        # Act
        web_service = WebService(api_key)
        result = await web_service.search(query, framework_name, framework_version)

        # Assert
        assert result == expected_answer
        mock_tavily_class.assert_called_once_with(api_key=api_key)
        mock_client.search.assert_called_once_with(
            query=query,
            include_answer="advanced",
            search_depth="advanced"
        )


@pytest.mark.asyncio
async def test_web_service_search_network_exception() -> None:
    # Arrange
    api_key = "test-tavily-key"
    query = "test query"
    framework_name = "test-framework"
    framework_version = "1.0.0"

    with patch("mcp_web_search.services.web.TavilyClient") as mock_tavily_class:
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.side_effect = Exception("Connection timed out")

        # Act
        web_service = WebService(api_key)
        result = await web_service.search(query, framework_name, framework_version)

        # Assert
        assert (
            result
            == "[MCP Error: Live web search currently unavailable. Overreaching fallback active.]"
        )
        mock_tavily_class.assert_called_once_with(api_key=api_key)


@pytest.mark.asyncio
async def test_web_service_search_missing_answer_field() -> None:
    # Arrange
    api_key = "test-tavily-key"
    query = "test query"
    framework_name = "test-framework"
    framework_version = "1.0.0"

    with patch("mcp_web_search.services.web.TavilyClient") as mock_tavily_class:
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        # Response is missing 'answer' key
        mock_client.search.return_value = {"results": []}

        # Act
        web_service = WebService(api_key)
        result = await web_service.search(query, framework_name, framework_version)

        # Assert
        assert (
            result
            == "[MCP Error: Live web search currently unavailable. Overreaching fallback active.]"
        )
        mock_tavily_class.assert_called_once_with(api_key=api_key)


@pytest.mark.asyncio
async def test_web_service_with_config_injection() -> None:
    # Arrange
    config = Config(
        TAVILY_API_KEY="config-tavily-key",
        OPENAI_API_KEY="test-openai-key"
    )
    query = "test query"
    framework_name = "test-framework"
    framework_version = "1.0.0"
    expected_answer = "Config search result."

    with patch("mcp_web_search.services.web.TavilyClient") as mock_tavily_class:
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = {"answer": expected_answer, "results": []}

        # Act
        web_service = WebService(config)
        result = await web_service.search(query, framework_name, framework_version)

        # Assert
        assert result == expected_answer
        mock_tavily_class.assert_called_once_with(api_key="config-tavily-key")
