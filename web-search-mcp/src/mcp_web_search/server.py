"""MCP Server definition and tool registration using FastMCP."""

import logging
from typing import Any
from pydantic import BaseModel
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from mcp_web_search.tools.web_search import web_search
from mcp_web_search.tools.db_search import db_search

logger = logging.getLogger("mcp_web_search")


class RequestResponseLoggingMiddleware(Middleware):
    async def on_message(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:
        msg = context.message
        if isinstance(msg, BaseModel):
            msg_str = msg.model_dump_json(exclude_none=True)
        else:
            msg_str = str(msg)

        logger.info(
            f"Incoming request/notification [method={context.method}, type={context.type}]: {msg_str}"
        )

        try:
            result = await call_next(context)

            if isinstance(result, BaseModel):
                res_str = result.model_dump_json(exclude_none=True)
            else:
                res_str = str(result)

            logger.info(f"Outgoing response for [method={context.method}]: {res_str}")
            return result
        except Exception as e:
            logger.error(
                f"Error processing [method={context.method}]: {e}", exc_info=True
            )
            raise e


# Create the FastMCP server instance
mcp = FastMCP("mcp-web-search")

# Register middleware
mcp.add_middleware(RequestResponseLoggingMiddleware())

# Register tools with FastMCP
mcp.tool()(web_search)
mcp.tool()(db_search)

# Dependency injection slot for the UsageTool instance
usage_tool_instance = None


@mcp.tool(name="usage")
async def usage() -> dict:
    """Get the current usage and cost statistics."""
    if usage_tool_instance is None:
        return {
            "total_web_searches": 0,
            "estimated_cost_usd": 0.0,
            "remaining_free_calls": 0,
        }
    return await usage_tool_instance()



