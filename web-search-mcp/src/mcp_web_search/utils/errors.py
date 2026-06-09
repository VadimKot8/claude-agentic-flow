"""Error definitions and formatting utilities for the MCP Web Search server."""


class MCPError(Exception):
    """Custom exception representing an MCP error with a category and detail.

    Attributes:
        category: The classification of the error (e.g., 'tavily', 'cache').
        detail: The detailed error message or underlying cause.
    """

    category: str
    detail: str

    def __init__(self, category: str, detail: str) -> None:
        super().__init__(f"[{category}] {detail}")
        self.category = category
        self.detail = detail


def format_error(category: str, detail: str) -> str:
    """Format an error category and details into a structured string.

    For 'tavily' failure category, returns the Spec §6 structured error string
    to be returned as tool output.

    Args:
        category: The category of the error.
        detail: The detailed error context.

    Returns:
        A structured string representing the error.
    """
    if category == "tavily":
        return "[MCP Error: Live web search currently unavailable. Overreaching fallback active.]"

    return f"[MCP Error: {category.capitalize()} error occurred. Details: {detail}]"


__all__ = ["MCPError", "format_error"]
