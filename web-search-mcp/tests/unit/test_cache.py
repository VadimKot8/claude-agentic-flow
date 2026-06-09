import pytest
import time
from unittest.mock import MagicMock, patch
from mcp_web_search.config import Config
from mcp_web_search.services.cache import CacheService, CacheHit
from mcp_web_search.services.embedder import ChromaEmbedder
from mcp_web_search.utils.errors import MCPError
from mcp_web_search.utils.hashing import compute_id
from mcp_web_search.llm.base import Embeddings


class DummyEmbeddings(Embeddings):
    """A dummy implementation of the Embeddings protocol for testing with real ChromaDB."""
    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Just return some dummy embeddings vector based on string properties
        return [[float(len(text)), 1.0, 2.0] for text in texts]


@pytest.mark.asyncio
async def test_cache_service_initialization_error() -> None:
    config = Config(
        TAVILY_API_KEY="test-tavily-key",
    )
    mock_embedder = MagicMock(spec=ChromaEmbedder)

    with patch("chromadb.PersistentClient", side_effect=Exception("Initialization failed")):
        with pytest.raises(MCPError, match="Failed to initialize ChromaDB PersistentClient"):
            CacheService(config, mock_embedder)


@pytest.mark.asyncio
async def test_cache_service_get_collection_error() -> None:
    config = Config(
        TAVILY_API_KEY="test-tavily-key",
    )
    mock_embedder = MagicMock(spec=ChromaEmbedder)

    with patch("chromadb.PersistentClient") as mock_persistent_client:
        mock_client = MagicMock()
        mock_persistent_client.return_value = mock_client
        mock_client.get_or_create_collection.side_effect = Exception("Collection creation failed")

        cache_service = CacheService(config, mock_embedder)
        with pytest.raises(MCPError, match="Failed to get or create collection"):
            await cache_service.upsert(
                simplified_query="simplified query text",
                framework_name="react",
                framework_version="18.0.0",
                answer="This is a cached answer",
                embedding=[0.1, 0.2, 0.3]
            )


@pytest.mark.asyncio
async def test_query_error_handling() -> None:
    config = Config(TAVILY_API_KEY="test-tavily-key")
    mock_embedder = MagicMock(spec=ChromaEmbedder)

    with patch("chromadb.PersistentClient") as mock_persistent_client:
        mock_client = MagicMock()
        mock_persistent_client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        mock_collection.query.side_effect = Exception("Chroma query failed")

        cache_service = CacheService(config, mock_embedder)
        with pytest.raises(MCPError, match="Failed to query cache entry"):
            await cache_service.query([0.1, 0.2], "react", "18.0.0")


@pytest.mark.asyncio
async def test_cache_service_real_chroma_upsert_query_hit(tmp_path) -> None:
    # (a) upsert then query returns hit
    config = Config(
        TAVILY_API_KEY="test-tavily-key",
        CHROMA_PATH=str(tmp_path),
        CHROMA_COLLECTION="test_collection",
        CACHE_TTL_DAYS=30,
        SIMILARITY_THRESHOLD=0.85
    )
    embeddings = DummyEmbeddings()
    embedder = ChromaEmbedder(embeddings)
    cache_service = CacheService(config, embedder)

    await cache_service.upsert(
        simplified_query="how to instantiate agent",
        framework_name="react",
        framework_version="18.0.0",
        answer="instantiate by calling agent()",
        embedding=[0.1, 0.2, 0.3]
    )

    hit = await cache_service.query([0.1, 0.2, 0.3], "react", "18.0.0")
    assert hit is not None
    assert hit.answer == "instantiate by calling agent()"
    assert hit.similarity_score >= 0.85


@pytest.mark.asyncio
async def test_cache_service_real_chroma_version_mismatch(tmp_path) -> None:
    # (b) version mismatch returns None
    config = Config(
        TAVILY_API_KEY="test-tavily-key",
        CHROMA_PATH=str(tmp_path),
        CHROMA_COLLECTION="test_collection",
        CACHE_TTL_DAYS=30,
        SIMILARITY_THRESHOLD=0.85
    )
    embeddings = DummyEmbeddings()
    embedder = ChromaEmbedder(embeddings)
    cache_service = CacheService(config, embedder)

    await cache_service.upsert(
        simplified_query="how to instantiate agent",
        framework_name="react",
        framework_version="18.0.0",
        answer="instantiate by calling agent()",
        embedding=[0.1, 0.2, 0.3]
    )

    # Different version
    hit_diff_version = await cache_service.query([0.1, 0.2, 0.3], "react", "19.0.0")
    assert hit_diff_version is None

    # Different framework
    hit_diff_framework = await cache_service.query([0.1, 0.2, 0.3], "vue", "18.0.0")
    assert hit_diff_framework is None


@pytest.mark.asyncio
async def test_cache_service_real_chroma_ttl_expiration(tmp_path) -> None:
    # (c) record older than TTL is deleted and returns None
    config = Config(
        TAVILY_API_KEY="test-tavily-key",
        CHROMA_PATH=str(tmp_path),
        CHROMA_COLLECTION="test_collection",
        CACHE_TTL_DAYS=30,
        SIMILARITY_THRESHOLD=0.85
    )
    embeddings = DummyEmbeddings()
    embedder = ChromaEmbedder(embeddings)
    cache_service = CacheService(config, embedder)

    # Upsert with mock time (31 days ago)
    expired_time = 1000000.0 - (31 * 24 * 60 * 60)
    with patch("mcp_web_search.services.cache.time.time", return_value=expired_time):
        await cache_service.upsert(
            simplified_query="how to instantiate agent",
            framework_name="react",
            framework_version="18.0.0",
            answer="instantiate by calling agent()",
            embedding=[0.1, 0.2, 0.3]
        )

    # Query with normal/current mock time (1000000.0)
    with patch("mcp_web_search.services.cache.time.time", return_value=1000000.0):
        hit = await cache_service.query([0.1, 0.2, 0.3], "react", "18.0.0")
        assert hit is None

    # Verify it was deleted (should return None even at the expired timestamp now because it was deleted from db)
    with patch("mcp_web_search.services.cache.time.time", return_value=expired_time):
        hit_after_deletion = await cache_service.query([0.1, 0.2, 0.3], "react", "18.0.0")
        assert hit_after_deletion is None


@pytest.mark.asyncio
async def test_cache_service_real_chroma_similarity_below_threshold(tmp_path) -> None:
    # (d) similarity below threshold returns None
    config = Config(
        TAVILY_API_KEY="test-tavily-key",
        CHROMA_PATH=str(tmp_path),
        CHROMA_COLLECTION="test_collection",
        CACHE_TTL_DAYS=30,
        SIMILARITY_THRESHOLD=0.9
    )
    embeddings = DummyEmbeddings()
    embedder = ChromaEmbedder(embeddings)
    cache_service = CacheService(config, embedder)

    # The collection uses cosine space, so similarity_score = 1 - cosine_distance
    # = cosine_similarity. We need cosine_similarity < 0.9 to stay below threshold.
    # Upsert an embedding pointing along the x-axis.
    await cache_service.upsert(
        simplified_query="how to instantiate agent",
        framework_name="react",
        framework_version="18.0.0",
        answer="instantiate by calling agent()",
        embedding=[1.0, 0.0, 0.0]
    )

    # Query with a vector at 45 degrees to the stored one.
    # cosine([1,0,0], [1,1,0]) = 1 / sqrt(2) ≈ 0.707 (< 0.9), so it should not hit.
    hit = await cache_service.query([1.0, 1.0, 0.0], "react", "18.0.0")
    assert hit is None
