import pytest
from typing import Any
from mcp_web_search.llm.base import Embeddings
from mcp_web_search.services.embedder import ChromaEmbedder


class MockEmbeddings(Embeddings):
    """A mock implementation of the Embeddings protocol for testing."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        # Generate dummy vector based on length of each text
        return [[float(len(text)), 1.0, 2.0] for text in texts]


@pytest.mark.asyncio
async def test_chroma_embedder_async() -> None:
    # Arrange
    mock_embeddings = MockEmbeddings()
    embedder = ChromaEmbedder(mock_embeddings)

    # Act
    result = await embedder.embed_async(["hello", "world"])

    # Assert
    assert len(result) == 2
    assert result[0] == [5.0, 1.0, 2.0]
    assert result[1] == [5.0, 1.0, 2.0]
    assert mock_embeddings.calls == [["hello", "world"]]


@pytest.mark.asyncio
async def test_chroma_embedder_sync_call_from_async_loop() -> None:
    # Arrange
    mock_embeddings = MockEmbeddings()
    embedder = ChromaEmbedder(mock_embeddings)

    # Act
    # This runs within the pytest-asyncio event loop, testing that the sync call
    # successfully bridges to the background thread loop without raising
    # "event loop already running" errors.
    result = embedder(["sync", "test"])

    # Assert
    assert len(result) == 2
    assert list(result[0]) == [4.0, 1.0, 2.0]
    assert list(result[1]) == [4.0, 1.0, 2.0]
    assert mock_embeddings.calls == [["sync", "test"]]


def test_chroma_embedder_sync_call_no_loop() -> None:
    # Arrange
    mock_embeddings = MockEmbeddings()
    embedder = ChromaEmbedder(mock_embeddings)

    # Act
    result = embedder(["no", "loop"])

    # Assert
    assert len(result) == 2
    assert list(result[0]) == [2.0, 1.0, 2.0]
    assert list(result[1]) == [4.0, 1.0, 2.0]
    assert mock_embeddings.calls == [["no", "loop"]]


def test_chroma_embedder_metadata() -> None:
    # Arrange
    mock_embeddings = MockEmbeddings()
    embedder = ChromaEmbedder(mock_embeddings)

    # Assert
    assert embedder.name() == "chroma_embedder"
    assert embedder.get_config() == {}

    with pytest.raises(ValueError, match="ChromaEmbedder must be constructed with an injected Embeddings instance"):
        ChromaEmbedder.build_from_config({})
