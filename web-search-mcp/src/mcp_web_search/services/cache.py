import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

import chromadb
from mcp_web_search.config import Config
from mcp_web_search.services.embedder import ChromaEmbedder
from mcp_web_search.utils.errors import MCPError
from mcp_web_search.utils.hashing import compute_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CacheHit:
    answer: str
    timestamp: int
    similarity_score: float


class CacheService:
    """Service handling caching using ChromaDB."""

    def __init__(self, config: Config, embedder: ChromaEmbedder) -> None:
        """Initialize the CacheService.

        Args:
            config: Configuration instance.
            embedder: Embedder instance (ChromaEmbedder).
        """
        self.config = config
        self.embedder = embedder
        try:
            self.client = chromadb.PersistentClient(path=self.config.CHROMA_PATH)
        except Exception as e:
            raise MCPError("cache", f"Failed to initialize ChromaDB PersistentClient: {e}") from e
        self._collection = None
        self._lock = asyncio.Lock()

    async def _get_collection(self) -> Any:
        """Lazily initialize and return the ChromaDB collection using asyncio.to_thread."""
        async with self._lock:
            if self._collection is None:
                try:
                    # Pin the HNSW index to cosine distance. Without this, Chroma
                    # defaults to (squared) L2, which makes `similarity = 1 - distance`
                    # incorrect for our normalized embeddings and silently sinks
                    # semantically-similar queries below the threshold. With cosine
                    # space, `distance = 1 - cosine_similarity`, so `1 - distance`
                    # is exactly the cosine similarity.
                    self._collection = await asyncio.to_thread(
                        self.client.get_or_create_collection,
                        name=self.config.CHROMA_COLLECTION,
                        embedding_function=self.embedder,
                        metadata={"hnsw:space": "cosine"},
                    )
                except Exception as e:
                    raise MCPError("cache", f"Failed to get or create collection: {e}") from e
            return self._collection

    async def upsert(
        self,
        simplified_query: str,
        framework_name: str,
        framework_version: str,
        answer: str,
        embedding: list[float],
    ) -> None:
        """Upsert a document into the ChromaDB collection.

        Args:
            simplified_query: The simplified query text.
            framework_name: The name of the framework.
            framework_version: The version of the framework.
            answer: The answer to cache.
            embedding: The embedding vector for the query.
        """
        try:
            collection = await self._get_collection()
            doc_id = compute_id(
                simplified_query=simplified_query,
                framework_name=framework_name,
                framework_version=framework_version,
            )
            metadata = {
                "timestamp": int(time.time()),
                "framework_name": framework_name,
                "framework_version": framework_version,
                "answer": answer,
            }
            await asyncio.to_thread(
                collection.upsert,
                ids=[doc_id],
                embeddings=[embedding],
                documents=[simplified_query],
                metadatas=[metadata],
            )
            logger.info(
                "cache upsert (stored to db): id=%s document=%r framework_name=%r "
                "framework_version=%r timestamp=%s answer=%r",
                doc_id,
                simplified_query,
                framework_name,
                framework_version,
                metadata["timestamp"],
                answer,
            )
        except MCPError:
            raise
        except Exception as e:
            raise MCPError("cache", f"Failed to upsert cache entry: {e}") from e

    async def query(
        self,
        embedded_query: list[float],
        framework_name: str,
        framework_version: str,
    ) -> CacheHit | None:
        """Query the cache for a similar query.

        Args:
            embedded_query: The embedding vector for the query.
            framework_name: The name of the framework.
            framework_version: The version of the framework.

        Returns:
            The CacheHit if found, valid, and not expired; otherwise None.
        """
        try:
            collection = await self._get_collection()
            results = await asyncio.to_thread(
                collection.query,
                query_embeddings=[embedded_query],
                where={
                    "$and": [
                        {"framework_name": framework_name},
                        {"framework_version": framework_version},
                    ]
                },
                n_results=1,
            )

            ids = results.get("ids")
            if not ids or len(ids[0]) == 0:
                return None

            hit_id = ids[0][0]

            distances = results.get("distances")
            metadatas = results.get("metadatas")

            if not distances or not metadatas or len(distances[0]) == 0 or len(metadatas[0]) == 0:
                return None

            distance = distances[0][0]
            metadata = metadatas[0][0]

            if metadata is None:
                return None

            answer = metadata.get("answer")
            timestamp = metadata.get("timestamp")
            if answer is None or timestamp is None:
                return None

            try:
                timestamp = int(timestamp)
            except (ValueError, TypeError):
                return None

            try:
                distance = float(distance)
            except (ValueError, TypeError):
                return None

            similarity_score = 1.0 - distance
            logger.info(
                "cache query (retrieved from db): id=%s similarity_score=%s timestamp=%s answer=%r",
                hit_id,
                similarity_score,
                timestamp,
                answer,
            )
            if similarity_score < self.config.SIMILARITY_THRESHOLD:
                logger.info(
                    "cache query: id=%s rejected (similarity_score=%s < threshold=%s)",
                    hit_id,
                    similarity_score,
                    self.config.SIMILARITY_THRESHOLD,
                )
                return None

            current_time = time.time()
            ttl_seconds = self.config.CACHE_TTL_DAYS * 24 * 60 * 60
            if current_time - timestamp > ttl_seconds:
                await asyncio.to_thread(collection.delete, ids=[hit_id])
                logger.info(
                    "cache query: id=%s stale-evicted (age=%ss > ttl=%ss)",
                    hit_id,
                    int(current_time - timestamp),
                    ttl_seconds,
                )
                return None

            logger.info("cache query: id=%s returned as fresh hit", hit_id)
            return CacheHit(
                answer=answer,
                timestamp=timestamp,
                similarity_score=similarity_score,
            )
        except MCPError:
            raise
        except Exception as e:
            raise MCPError("cache", f"Failed to query cache entry: {e}") from e
