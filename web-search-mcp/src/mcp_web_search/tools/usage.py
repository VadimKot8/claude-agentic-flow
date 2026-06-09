"""Tool handler for the usage MCP tool."""

from mcp_web_search.services.metrics import Metrics
from mcp_web_search.config import Config


class UsageTool:
    """Zero-argument async tool handler for tracking usage and cost metrics.

    Takes Metrics and Config via constructor injection.
    """

    def __init__(self, metrics: Metrics, config: Config) -> None:
        self.metrics = metrics
        self.config = config

    async def __call__(self) -> dict:
        """Execute the tool to get current usage statistics.

        Returns:
            A dictionary representing the JSON object with usage metrics.
        """
        snapshot = await self.metrics.snapshot()
        total_web_searches = snapshot.get("total_web_searches", 0)

        # Safely get configuration values from class or instance
        cost_per_search = getattr(
            self.config, "TAVILY_COST_PER_SEARCH_USD", 0.0
        )
        free_tier_allocation = getattr(
            self.config, "TAVILY_FREE_TIER_ALLOCATION", 0
        )

        estimated_cost_usd = total_web_searches * cost_per_search
        remaining_free_calls = max(0, free_tier_allocation - total_web_searches)

        return {
            "total_web_searches": total_web_searches,
            "estimated_cost_usd": estimated_cost_usd,
            "remaining_free_calls": remaining_free_calls,
        }
