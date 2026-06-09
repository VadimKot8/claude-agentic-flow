import logging
from typing import Any, Dict

from mcp_web_search.services.embedder import ChromaEmbedder
from mcp_web_search.services.cache import CacheService
from mcp_web_search.services.summarizer import Summarizer

logger = logging.getLogger(__name__)

# Module-level dependencies injected at startup
embedder: ChromaEmbedder | None = None
cache_service: CacheService | None = None
summarizer: Summarizer | None = None


async def db_search(
    query: str,
    framework_name: str,
    framework_version: str
) -> Dict[str, Any]:
    """Search the local vector cache for a previously cached answer.

    This tool is strictly read-only from the cache and never calls Tavily or falls through
    to web_search. If a cache miss or any error occurs, it logs a warning and returns
    status="cache_miss".

    Args:
        query: The raw search query.
        framework_name: The name of the framework context.
        framework_version: The version of the framework.

    Returns:
        A dictionary indicating either a success (with answer, timestamp, and similarity score)
        or a cache miss.
    """
    logger.info(
        "db_search request: query=%r framework_name=%r framework_version=%r",
        query,
        framework_name,
        framework_version,
    )

    if embedder is None or cache_service is None:
        logger.warning("db_search called but dependencies are not initialized.")
        logger.info("db_search response: status=cache_miss (dependencies not initialized)")
        return {"status": "cache_miss"}

    try:
        # 1. Simplify the query so the read side matches the write side. The cache
        # stores embeddings of the *simplified* query; embedding the raw query here
        # would compare against a different phrasing and depress similarity for
        # paraphrased re-asks. Falling back to the raw query keeps reads working even
        # if summarization fails (degraded cache must never block the agent).
        search_query = query
        if summarizer is not None:
            try:
                simplified = await summarizer.simplify(query)
                if simplified and simplified.strip():
                    search_query = simplified
                    logger.info(
                        "db_search simplified query: raw=%r -> simplified=%r",
                        query,
                        search_query,
                    )
            except Exception as e:
                logger.warning(
                    "db_search summarization failed; falling back to raw query: %s",
                    e,
                )

        # 2. Embed the (simplified) query (async path)
        embeddings = await embedder.embed_async([search_query])
        if not embeddings or not embeddings[0]:
            logger.warning("Embedder returned empty embeddings for query: %s", search_query)
            logger.info("db_search response: status=cache_miss (empty embeddings)")
            return {"status": "cache_miss"}
        vector = embeddings[0]

        # 3. Call CacheService.query to check the database
        hit = await cache_service.query(
            embedded_query=vector,
            framework_name=framework_name,
            framework_version=framework_version
        )

        if hit is None:
            logger.info("db_search response: status=cache_miss")
            return {"status": "cache_miss"}

        logger.info(
            "db_search response: status=success similarity_score=%s timestamp=%s answer=%r",
            hit.similarity_score,
            hit.timestamp,
            hit.answer,
        )
        return {
            "status": "success",
            "answer": hit.answer,
            "timestamp": hit.timestamp,
            "similarity_score": hit.similarity_score
        }
    except Exception as e:
        logger.warning("Error during db_search cache retrieval: %s", e, exc_info=True)
        logger.info("db_search response: status=cache_miss (error)")
        return {"status": "cache_miss"}
