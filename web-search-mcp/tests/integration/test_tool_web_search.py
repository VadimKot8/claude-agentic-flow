"""Integration tests for the web_search MCP tool."""

import pytest
from unittest.mock import MagicMock, patch
from fastmcp import Client
from mcp_web_search.server import mcp
import mcp_web_search.tools.web_search as web_search_tool
from mcp_web_search.services.web import WebService
from mcp_web_search.services.metrics import Metrics


@pytest.mark.asyncio
async def test_integration_web_search_tool() -> None:
    # Arrange
    # Set up real instances of services with dummy configuration keys
    mock_web_service = WebService("test-api-key")
    mock_metrics = Metrics()

    # Inject dependencies
    web_search_tool.web_service = mock_web_service
    web_search_tool.metrics = mock_metrics

    try:
        # Mock the internal TavilyClient.search call
        with patch("mcp_web_search.services.web.TavilyClient") as mock_tavily_class:
            mock_client = MagicMock()
            mock_tavily_class.return_value = mock_client
            mock_client.search.return_value = {
                "answer": "Integration Test Answer",
                "results": [],
            }

            # Act: Use FastMCP Client to execute the tool in-process
            async with Client(mcp) as client:
                # Retrieve registered tools to verify registration
                tools = await client.list_tools()
                assert any(tool.name == "web_search" for tool in tools)

                # Call the tool using client.call_tool
                result = await client.call_tool(
                    "web_search",
                    arguments={
                        "query": "what is mcp",
                        "framework_name": "fastmcp",
                        "framework_version": "1.0.0",
                    },
                )

            # Assert
            assert result.data == "Integration Test Answer"
            mock_tavily_class.assert_called_once_with(api_key="test-api-key")
            mock_client.search.assert_called_once_with(
                query="what is mcp",
                include_answer="advanced",
                search_depth="advanced",
            )
    finally:
        # Clean up global tool variables
        web_search_tool.web_service = None
        web_search_tool.metrics = None
