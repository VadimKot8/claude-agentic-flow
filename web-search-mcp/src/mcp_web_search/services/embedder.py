import asyncio
import threading
import warnings
from typing import Any, cast

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings as ChromaEmbeddings
from mcp_web_search.llm.base import Embeddings


class ChromaEmbedder(EmbeddingFunction[Documents]):
    """
    ChromaEmbedder bridges ChromaDB's synchronous EmbeddingFunction interface
    with the project's asynchronous Embeddings protocol.

    Why this design?
    ChromaDB's collection APIs (like collection.add or collection.query) are synchronous
    and expect a synchronous EmbeddingFunction. However, modern LLM clients (like OpenAI)
    are asynchronous and run inside an async event loop (like the FastMCP server).
    
    To handle this without blocking the server's main event loop or causing "event loop
    already running" errors, we expose both:
    1. A synchronous `__call__` method implementing ChromaDB's EmbeddingFunction protocol.
       It uses a dedicated event loop running in a background thread to execute the async
       embeddings call synchronously.
    2. An asynchronous `embed_async` helper that can be called directly by async search/cache
       services (e.g. `db_search` or `CacheService`) to keep the call stack fully async and
       highly performant.
    """

    def __init__(self, embedder: Embeddings) -> None:
        """Initialize the ChromaEmbedder with the underlying async Embeddings service."""
        self.embedder = embedder
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def __del__(self) -> None:
        try:
            if hasattr(self, "_loop") and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            if hasattr(self, "_thread") and self._thread.is_alive():
                self._thread.join(timeout=1.0)
        except Exception:
            pass

    async def embed_async(self, input: list[str]) -> list[list[float]]:
        """Asynchronously embed a list of texts, preserving the async call stack."""
        return await self.embedder.embed(input)

    def __call__(self, input: Documents) -> ChromaEmbeddings:
        """Synchronous adapter for ChromaDB's collection calls."""
        # Ensure we work with list of strings
        texts = list(input)
        future = asyncio.run_coroutine_threadsafe(
            self.embedder.embed(texts),
            self._loop
        )
        return cast(ChromaEmbeddings, future.result())

    @staticmethod
    def name() -> str:
        """Return the embedding function name."""
        return "chroma_embedder"

    def get_config(self) -> dict[str, Any]:
        """Return a serializable configuration for the embedding function."""
        return {}

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "ChromaEmbedder":
        """Build an embedding function from a serialized config."""
        # Note: Since the real Embeddings provider cannot be easily reconstructed
        # from a blank config, this raises a ValueError if called without a real instance.
        raise ValueError("ChromaEmbedder must be constructed with an injected Embeddings instance.")
