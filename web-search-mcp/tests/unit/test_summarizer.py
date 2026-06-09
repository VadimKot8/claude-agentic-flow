import pytest
from unittest.mock import AsyncMock
from mcp_web_search.services.summarizer import Summarizer
from mcp_web_search.llm.base import ChatLLM


class MockChatLLM(ChatLLM):
    def __init__(self) -> None:
        self.complete_mock = AsyncMock()

    async def complete(self, system: str, user: str) -> str:
        return await self.complete_mock(system, user)


@pytest.mark.asyncio
async def test_summarizer_simplify_success() -> None:
    # Arrange
    mock_llm = MockChatLLM()
    mock_llm.complete_mock.return_value = "python async task handling"
    summarizer = Summarizer(mock_llm)
    raw_query = "Error: Task was destroyed but it is pending! traceback... please help me fix this in python"

    # Act
    result = await summarizer.simplify(raw_query)

    # Assert
    assert result == "python async task handling"
    mock_llm.complete_mock.assert_called_once()
    system_arg, user_arg = mock_llm.complete_mock.call_args[0]
    assert "search query summarizer" in system_arg
    assert user_arg == raw_query


@pytest.mark.asyncio
async def test_summarizer_simplify_strips_quotes_and_whitespace() -> None:
    # Arrange
    mock_llm = MockChatLLM()
    mock_llm.complete_mock.return_value = '  "python async task handling"  '
    summarizer = Summarizer(mock_llm)

    # Act
    result = await summarizer.simplify("some query")

    # Assert
    assert result == "python async task handling"


@pytest.mark.asyncio
async def test_summarizer_simplify_empty_input() -> None:
    # Arrange
    mock_llm = MockChatLLM()
    summarizer = Summarizer(mock_llm)

    # Act & Assert
    assert await summarizer.simplify("") == ""
    assert await summarizer.simplify("   ") == ""
    mock_llm.complete_mock.assert_not_called()
