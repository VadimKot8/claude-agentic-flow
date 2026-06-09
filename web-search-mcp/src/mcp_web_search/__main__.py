"""Entrypoint for the MCP Web Search server."""

import sys
import logging
from mcp_web_search.config import Config
from mcp_web_search.llm.openai_provider import OpenAIChatLLM, OpenAIEmbeddings
from mcp_web_search.services.summarizer import Summarizer
from mcp_web_search.services.embedder import ChromaEmbedder
from mcp_web_search.services.cache import CacheService
from mcp_web_search.services.background import BackgroundWriter
from mcp_web_search.services.web import WebService
from mcp_web_search.services.metrics import Metrics

import mcp_web_search.tools.web_search as web_search_tool
import mcp_web_search.tools.db_search as db_search_tool
from mcp_web_search.server import mcp


def main() -> None:
    """Bootstrap and run the MCP server."""
    try:
        # 1. Load configuration from environment
        config = Config.from_env()

        # Configure logging level
        logging.basicConfig(
            level=config.LOG_LEVEL,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            force=True,
        )
        logging.getLogger().setLevel(config.LOG_LEVEL)
        logging.getLogger("mcp_web_search").setLevel(config.LOG_LEVEL)
        logging.getLogger("mcp").setLevel(config.LOG_LEVEL)

        # Inject into uvicorn logging config to prevent uvicorn overrides from silencing loggers
        try:
            import uvicorn.config

            uvicorn.config.LOGGING_CONFIG["loggers"]["mcp_web_search"] = {
                "handlers": ["default"],
                "level": config.LOG_LEVEL,
                "propagate": False,
            }
            uvicorn.config.LOGGING_CONFIG["loggers"]["mcp"] = {
                "handlers": ["default"],
                "level": config.LOG_LEVEL,
                "propagate": False,
            }
        except ImportError:
            pass

        # 2. Construct LLM instances
        openai_chat_llm = OpenAIChatLLM(api_key=config.OPENAI_API_KEY, model_name=config.SUMMARIZATION_MODEL)
        openai_embeddings = OpenAIEmbeddings(api_key=config.OPENAI_API_KEY, model_name=config.EMBEDDING_MODEL)

        # 3. Construct services
        summarizer = Summarizer(llm=openai_chat_llm)
        embedder = ChromaEmbedder(embedder=openai_embeddings)
        cache_service = CacheService(config=config, embedder=embedder)
        background_writer = BackgroundWriter(
            summarizer=summarizer,
            embedder=embedder,
            cache_service=cache_service,
        )

        web_service = WebService(config)
        metrics = Metrics()

        # 4. Inject dependencies into tool handlers
        web_search_tool.web_service = web_service
        web_search_tool.metrics = metrics
        web_search_tool.background_writer = background_writer

        db_search_tool.embedder = embedder
        db_search_tool.cache_service = cache_service
        db_search_tool.summarizer = summarizer

        from mcp_web_search.tools.usage import UsageTool
        import mcp_web_search.server as server_mod
        server_mod.usage_tool_instance = UsageTool(metrics=metrics, config=config)

        # 5. Start the server using the configured host and port
        print(
            f"Starting MCP Web Search server on http://{config.MCP_HTTP_HOST}:{config.MCP_HTTP_PORT}"
        )
        mcp.run(
            transport="streamable-http",
            host=config.MCP_HTTP_HOST,
            port=config.MCP_HTTP_PORT,
        )
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

