import asyncio
import logging
from typing import Any, Set

logger = logging.getLogger(__name__)

# Module-level set to keep references to active background tasks alive, preventing garbage collection
_BACKGROUND_TASKS: Set[asyncio.Task] = set()


class BackgroundWriter:
    """Service that executes the asynchronous caching pipeline in the background.

    This class orchestrates a pipeline that simplifies a query, embeds the simplified query,
    and caches the resulting embedding and metadata in the cache service.
    """

    def __init__(self, summarizer: Any, embedder: Any, cache_service: Any) -> None:
        """Initialize the BackgroundWriter with its dependencies.

        Args:
            summarizer: The service used to simplify queries.
            embedder: The service used to embed text.
            cache_service: The service used to upsert records into ChromaDB.
        """
        self.summarizer = summarizer
        self.embedder = embedder
        self.cache_service = cache_service

    def enqueue(
        self,
        raw_query: str,
        framework_name: str,
        framework_version: str,
        answer: str
    ) -> None:
        """Enqueue a background caching task for a resolved query.

        This method is synchronous and non-blocking. It schedules the async pipeline
        (summarize -> embed -> cache.upsert) to run in the background event loop.

        Args:
            raw_query: The original, potentially verbose query.
            framework_name: The name of the framework context.
            framework_version: The version of the framework.
            answer: The answer content retrieved from the web search.
        """
        task = asyncio.create_task(
            self._write_pipeline(raw_query, framework_name, framework_version, answer)
        )
        _BACKGROUND_TASKS.add(task)
        task.add_done_callback(_BACKGROUND_TASKS.discard)

    async def _write_pipeline(
        self,
        raw_query: str,
        framework_name: str,
        framework_version: str,
        answer: str
    ) -> None:
        """Execute the asynchronous caching pipeline.

        All exceptions raised within this pipeline are caught and logged at the WARN level,
        ensuring they do not propagate or interrupt the calling thread.
        """
        try:
            # 1. Summarize: Simplify the raw query
            simplified = await self.summarizer.simplify(raw_query)

            # 2. Embed: Get the vector representation of the simplified query
            embeddings = await self.embedder.embed_async([simplified])
            if not embeddings or not embeddings[0]:
                raise ValueError("Embedder returned empty embeddings for the simplified query.")
            vector = embeddings[0]

            # 3. Cache: Upsert the document and metadata into the cache
            await self.cache_service.upsert(
                simplified_query=simplified,
                framework_name=framework_name,
                framework_version=framework_version,
                answer=answer,
                embedding=vector
            )
        except Exception as e:
            logger.warning("Background caching pipeline failed: %s", e, exc_info=True)
