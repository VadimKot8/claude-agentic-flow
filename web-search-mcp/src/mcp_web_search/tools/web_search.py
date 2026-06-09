"""Tool handler for the web_search MCP tool."""

import logging

from mcp_web_search.services.web import WebService
from mcp_web_search.services.metrics import Metrics
from mcp_web_search.services.background import BackgroundWriter

logger = logging.getLogger(__name__)

# Module-level dependency injection slots.
# These will be populated at startup by the main entrypoint.
web_service: WebService | None = None
metrics: Metrics | None = None
background_writer: BackgroundWriter | None = None


async def web_search(query: str, framework_name: str, framework_version: str) -> str:
    """Search the web for real-time technical answers using Tavily.

    Args:
        query: The technical question or search query.
        framework_name: The name of the tool/library currently being used.
        framework_version: The target version context of the tool/library.

    Returns:
        The extracted answer text from Tavily or a formatted error message.
    """
    logger.info(
        "web_search request: query=%r framework_name=%r framework_version=%r",
        query,
        framework_name,
        framework_version,
    )

    if not web_service:
        from mcp_web_search.utils.errors import format_error

        return format_error("tavily", "WebService dependency is not initialized.")

    answer = await web_service.search(
        query=query,
        framework_name=framework_name,
        framework_version=framework_version,
    )

    is_success = not answer.startswith("[MCP Error")

    logger.info(
        "web_search response: success=%s answer=%r",
        is_success,
        answer,
    )

    if metrics and is_success:
        await metrics.increment_web_search()

    if background_writer and is_success:
        background_writer.enqueue(
            raw_query=query,
            framework_name=framework_name,
            framework_version=framework_version,
            answer=answer,
        )

    return answer

