"""Integration tests for the usage MCP tool."""

import pytest
from unittest.mock import MagicMock, patch
import json
from fastmcp import Client
from mcp_web_search.server import mcp
import mcp_web_search.tools.web_search as web_search_tool
import mcp_web_search.server as server_mod
from mcp_web_search.tools.usage import UsageTool
from mcp_web_search.services.web import WebService
from mcp_web_search.services.metrics import Metrics
from mcp_web_search.config import Config


@pytest.mark.asyncio
async def test_integration_usage_tool() -> None:
    # 1. Setup fresh config & metrics
    config = Config(
        TAVILY_API_KEY="test-tavily-key",
        TAVILY_COST_PER_SEARCH_USD=0.015,
        TAVILY_FREE_TIER_ALLOCATION=1000,
    )
    metrics = Metrics()
    web_service = WebService(config)

    # 2. Inject into the modules/server
    web_search_tool.web_service = web_service
    web_search_tool.metrics = metrics
    server_mod.usage_tool_instance = UsageTool(metrics=metrics, config=config)

    async with Client(mcp) as client:
        # (a) call usage on a fresh server and assert all three fields are zero/initial
        usage_res = await client.call_tool("usage", arguments={})
        usage_data = json.loads(usage_res.content[0].text)
        assert usage_data["total_web_searches"] == 0
        assert usage_data["estimated_cost_usd"] == 0.0
        assert usage_data["remaining_free_calls"] == 1000

        # (b) trigger K successful web_search calls (mocked Tavily), then call usage
        # and assert total_web_searches=K, estimated_cost_usd ≈ K * cost_per_search, remaining_free_calls = allocation - K
        k = 3
        with patch("mcp_web_search.services.web.TavilyClient") as mock_tavily_class:
            mock_client = MagicMock()
            mock_tavily_class.return_value = mock_client
            mock_client.search.return_value = {
                "answer": "Successful mock Tavily search result."
            }

            for _ in range(k):
                web_res = await client.call_tool(
                    "web_search",
                    arguments={
                        "query": "test query",
                        "framework_name": "pytest",
                        "framework_version": "8.0.0",
                    }
                )
                assert not web_res.data.startswith("[MCP Error")

            usage_res_k = await client.call_tool("usage", arguments={})
            usage_data_k = json.loads(usage_res_k.content[0].text)
            assert usage_data_k["total_web_searches"] == k
            assert abs(usage_data_k["estimated_cost_usd"] - k * 0.015) < 1e-9
            assert usage_data_k["remaining_free_calls"] == 1000 - k

        # (c) trigger a web_search where Tavily fails and assert the counter did NOT increment
        with patch("mcp_web_search.services.web.TavilyClient") as mock_tavily_class:
            mock_client = MagicMock()
            mock_tavily_class.return_value = mock_client
            mock_client.search.side_effect = Exception("Tavily API Failure")

            failed_res = await client.call_tool(
                "web_search",
                arguments={
                    "query": "failed query",
                    "framework_name": "pytest",
                    "framework_version": "8.0.0",
                }
            )
            assert failed_res.data.startswith("[MCP Error")

            usage_res_fail = await client.call_tool("usage", arguments={})
            usage_data_fail = json.loads(usage_res_fail.content[0].text)
            # The count should still be k
            assert usage_data_fail["total_web_searches"] == k
            assert abs(usage_data_fail["estimated_cost_usd"] - k * 0.015) < 1e-9
            assert usage_data_fail["remaining_free_calls"] == 1000 - k

        # (d) restart the server (new Config + new Metrics instance) and assert the counter resets to zero.
        # We simulate this by constructing new instances and injecting them.
        new_config = Config(
            TAVILY_API_KEY="test-tavily-key",
            TAVILY_COST_PER_SEARCH_USD=0.015,
            TAVILY_FREE_TIER_ALLOCATION=1000,
        )
        new_metrics = Metrics()
        new_web_service = WebService(new_config)

        web_search_tool.web_service = new_web_service
        web_search_tool.metrics = new_metrics
        server_mod.usage_tool_instance = UsageTool(metrics=new_metrics, config=new_config)

        # Call usage again and assert they are reset to zero
        usage_res_reset = await client.call_tool("usage", arguments={})
        usage_data_reset = json.loads(usage_res_reset.content[0].text)
        assert usage_data_reset["total_web_searches"] == 0
        assert usage_data_reset["estimated_cost_usd"] == 0.0
        assert usage_data_reset["remaining_free_calls"] == 1000
