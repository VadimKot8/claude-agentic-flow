from typing import Protocol, runtime_checkable


@runtime_checkable
class ChatLLM(Protocol):
    """Protocol for Chat LLM providers."""

    async def complete(self, system: str, user: str) -> str:
        """Complete a chat prompt using system and user messages."""
        ...


@runtime_checkable
class Embeddings(Protocol):
    """Protocol for embedding providers."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vector representations."""
        ...
