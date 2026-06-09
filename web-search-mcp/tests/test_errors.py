from mcp_web_search.utils.errors import MCPError, format_error


def test_mcp_error_properties() -> None:
    """Test that MCPError stores category and detail correctly."""
    err = MCPError("cache", "connection timed out")
    assert err.category == "cache"
    assert err.detail == "connection timed out"
    assert str(err) == "[cache] connection timed out"


def test_format_error_tavily() -> None:
    """Test format_error with tavily category returns exact Spec §6 string."""
    result = format_error("tavily", "api limit reached")
    assert (
        result
        == "[MCP Error: Live web search currently unavailable. Overreaching fallback active.]"
    )


def test_format_error_other() -> None:
    """Test format_error with other categories returns standard formatted message."""
    result = format_error("cache", "disk full")
    assert "Cache error occurred" in result
    assert "disk full" in result
