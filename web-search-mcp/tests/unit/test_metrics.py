"""Unit tests for the Metrics class."""

import asyncio
import pytest
from mcp_web_search.services.metrics import Metrics


@pytest.mark.asyncio
async def test_metrics_concurrent_increments() -> None:
    # Arrange
    metrics = Metrics()
    n = 100

    # Act
    # Fire N concurrent increment_web_search() tasks
    tasks = [asyncio.create_task(metrics.increment_web_search()) for _ in range(n)]
    await asyncio.gather(*tasks)

    snapshot_val = await metrics.snapshot()

    # Assert
    assert isinstance(snapshot_val, dict)
    assert snapshot_val == {"total_web_searches": n}

