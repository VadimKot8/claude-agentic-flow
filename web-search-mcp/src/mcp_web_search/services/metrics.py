"""Operational metrics monitoring."""

import asyncio


class Metrics:
    """Operational metrics tracking.

    Maintains the public method signatures for incrementing searches and
    taking snapshot dictionaries.
    """

    def __init__(self) -> None:
        """Initialize the metrics tracker."""
        self._counter: int = 0
        self._lock = asyncio.Lock()

    async def increment_web_search(self) -> None:
        """Increment the web search counter."""
        async with self._lock:
            self._counter += 1

    async def snapshot(self) -> dict:
        """Get the current metrics snapshot.

        Returns:
            A dictionary containing total_web_searches.
        """
        async with self._lock:
            return {"total_web_searches": self._counter}

