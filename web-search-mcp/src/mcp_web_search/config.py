from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Supported LLM providers. Adding a new provider requires a concrete impl in
# llm/ and a branch in the __main__ factory.
SUPPORTED_LLM_PROVIDERS: frozenset[str] = frozenset({"openai"})

# Allowlists of models known to be valid per provider. An unknown model is
# rejected at startup rather than failing silently at first LLM call.
SUPPORTED_OPENAI_CHAT_MODELS: frozenset[str] = frozenset({
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
})
SUPPORTED_OPENAI_EMBEDDING_MODELS: frozenset[str] = frozenset({
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
})


@dataclass(frozen=True)
class Config:
    TAVILY_API_KEY: str
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    SUMMARIZATION_MODEL: str = "gpt-5-mini"
    CHROMA_PATH: str = "./.chroma"
    CHROMA_COLLECTION: str = "web_search_cache"
    CACHE_TTL_DAYS: int = 30
    SIMILARITY_THRESHOLD: float = 0.75
    TAVILY_COST_PER_SEARCH_USD: float = 0.015
    TAVILY_FREE_TIER_ALLOCATION: int = 1000
    MCP_HTTP_HOST: str = "127.0.0.1"
    MCP_HTTP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """Load and validate configuration from the environment and optional .env file.

        Raises:
            ValueError: If validation of required keys fails or types cannot be parsed.
        """
        # Load environment variables from .env file if it exists
        load_dotenv()

        # Retrieve and validate TAVILY_API_KEY
        tavily_api_key_raw = os.environ.get("TAVILY_API_KEY")
        if not tavily_api_key_raw or not tavily_api_key_raw.strip():
            raise ValueError(
                "Configuration error: TAVILY_API_KEY is required and cannot be empty."
            )
        tavily_api_key = tavily_api_key_raw.strip()

        # Retrieve and parse other fields with default values
        llm_provider = os.environ.get("LLM_PROVIDER", "openai").strip()
        if not llm_provider:
            llm_provider = "openai"

        # Validate the provider is one we actually implement.
        if llm_provider not in SUPPORTED_LLM_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_LLM_PROVIDERS))
            raise ValueError(
                f"Configuration error: LLM_PROVIDER {llm_provider!r} is not supported. "
                f"Supported providers: {supported}."
            )

        # Validate OPENAI_API_KEY if LLM_PROVIDER is "openai"
        openai_api_key_raw = os.environ.get("OPENAI_API_KEY")
        openai_api_key = openai_api_key_raw.strip() if openai_api_key_raw else None

        if llm_provider == "openai":
            if not openai_api_key:
                raise ValueError(
                    "Configuration error: OPENAI_API_KEY must be provided when LLM_PROVIDER is 'openai'."
                )

        embedding_model = os.environ.get(
            "EMBEDDING_MODEL", "text-embedding-3-small"
        ).strip()
        if not embedding_model:
            embedding_model = "text-embedding-3-small"

        summarization_model = os.environ.get(
            "SUMMARIZATION_MODEL", cls.SUMMARIZATION_MODEL
        ).strip()
        if not summarization_model:
            summarization_model = cls.SUMMARIZATION_MODEL

        # Validate model names against the provider's allowlist so a typo or an
        # unsupported model is caught at startup rather than at first LLM call.
        if llm_provider == "openai":
            if summarization_model not in SUPPORTED_OPENAI_CHAT_MODELS:
                supported = ", ".join(sorted(SUPPORTED_OPENAI_CHAT_MODELS))
                raise ValueError(
                    f"Configuration error: SUMMARIZATION_MODEL {summarization_model!r} is not a "
                    f"supported OpenAI chat model. Supported models: {supported}."
                )
            if embedding_model not in SUPPORTED_OPENAI_EMBEDDING_MODELS:
                supported = ", ".join(sorted(SUPPORTED_OPENAI_EMBEDDING_MODELS))
                raise ValueError(
                    f"Configuration error: EMBEDDING_MODEL {embedding_model!r} is not a "
                    f"supported OpenAI embedding model. Supported models: {supported}."
                )

        chroma_path = os.environ.get("CHROMA_PATH", "./.chroma").strip()
        if not chroma_path:
            chroma_path = "./.chroma"

        chroma_collection = os.environ.get(
            "CHROMA_COLLECTION", "web_search_cache"
        ).strip()
        if not chroma_collection:
            chroma_collection = "web_search_cache"

        # Integer parsing with fallback/error handling
        cache_ttl_days_raw = os.environ.get("CACHE_TTL_DAYS", "30").strip()
        if not cache_ttl_days_raw:
            cache_ttl_days = 30
        else:
            try:
                cache_ttl_days = int(cache_ttl_days_raw)
            except ValueError as e:
                raise ValueError(
                    f"Configuration error: CACHE_TTL_DAYS must be a valid integer, got {cache_ttl_days_raw!r}."
                ) from e

        tavily_free_tier_allocation_raw = os.environ.get(
            "TAVILY_FREE_TIER_ALLOCATION", "1000"
        ).strip()
        if not tavily_free_tier_allocation_raw:
            tavily_free_tier_allocation = 1000
        else:
            try:
                tavily_free_tier_allocation = int(tavily_free_tier_allocation_raw)
            except ValueError as e:
                raise ValueError(
                    f"Configuration error: TAVILY_FREE_TIER_ALLOCATION must be a valid integer, got {tavily_free_tier_allocation_raw!r}."
                ) from e

        mcp_http_port_raw = os.environ.get("MCP_HTTP_PORT", "8000").strip()
        if not mcp_http_port_raw:
            mcp_http_port = 8000
        else:
            try:
                mcp_http_port = int(mcp_http_port_raw)
            except ValueError as e:
                raise ValueError(
                    f"Configuration error: MCP_HTTP_PORT must be a valid integer, got {mcp_http_port_raw!r}."
                ) from e

        # Float parsing with fallback/error handling
        similarity_threshold_raw = os.environ.get(
            "SIMILARITY_THRESHOLD", "0.75"
        ).strip()
        if not similarity_threshold_raw:
            similarity_threshold = 0.75
        else:
            try:
                similarity_threshold = float(similarity_threshold_raw)
            except ValueError as e:
                raise ValueError(
                    f"Configuration error: SIMILARITY_THRESHOLD must be a valid float, got {similarity_threshold_raw!r}."
                ) from e

        tavily_cost_per_search_usd_raw = os.environ.get(
            "TAVILY_COST_PER_SEARCH_USD", "0.015"
        ).strip()
        if not tavily_cost_per_search_usd_raw:
            tavily_cost_per_search_usd = 0.015
        else:
            try:
                tavily_cost_per_search_usd = float(tavily_cost_per_search_usd_raw)
            except ValueError as e:
                raise ValueError(
                    f"Configuration error: TAVILY_COST_PER_SEARCH_USD must be a valid float, got {tavily_cost_per_search_usd_raw!r}."
                ) from e

        mcp_http_host = os.environ.get("MCP_HTTP_HOST", "127.0.0.1").strip()
        if not mcp_http_host:
            mcp_http_host = "127.0.0.1"

        log_level = os.environ.get("LOG_LEVEL", "INFO").upper().strip()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(
                f"Configuration error: LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL. Got {log_level!r}."
            )

        return cls(
            TAVILY_API_KEY=tavily_api_key,
            LLM_PROVIDER=llm_provider,
            OPENAI_API_KEY=openai_api_key,
            EMBEDDING_MODEL=embedding_model,
            SUMMARIZATION_MODEL=summarization_model,
            CHROMA_PATH=chroma_path,
            CHROMA_COLLECTION=chroma_collection,
            CACHE_TTL_DAYS=cache_ttl_days,
            SIMILARITY_THRESHOLD=similarity_threshold,
            TAVILY_COST_PER_SEARCH_USD=tavily_cost_per_search_usd,
            TAVILY_FREE_TIER_ALLOCATION=tavily_free_tier_allocation,
            MCP_HTTP_HOST=mcp_http_host,
            MCP_HTTP_PORT=mcp_http_port,
            LOG_LEVEL=log_level,
        )
