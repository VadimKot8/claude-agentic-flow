"""Web search service implementation using the Tavily API."""

import asyncio
from tavily import TavilyClient
from mcp_web_search.config import Config
from mcp_web_search.utils.errors import format_error


class WebService:
    """Service to interact with the Tavily Search API."""

    def __init__(self, api_key_or_config: str | Config) -> None:
        """Initialize the WebService with a Tavily API key or Config object.

        Args:
            api_key_or_config: Either a string (Tavily API key) or a Config instance containing the key.
        """
        if isinstance(api_key_or_config, Config):
            self.api_key = api_key_or_config.TAVILY_API_KEY
        else:
            self.api_key = api_key_or_config

    async def search(
        self, query: str, framework_name: str, framework_version: str
    ) -> str:
        """Execute a web search using Tavily API.

        Args:
            query: The search query.
            framework_name: The target framework name.
            framework_version: The target framework version.

        Returns:
            The extracted top-level 'answer' string from the Tavily response.
            On failure, returns a formatted error string.
        """
        try:
            if not self.api_key:
                raise ValueError("Tavily API key is missing or empty.")

            # Instantiates TavilyClient inside the try block to handle any key/initialization errors.
            client = TavilyClient(api_key=self.api_key)

            # Perform the synchronous Tavily search within asyncio.to_thread to avoid blocking the event loop.
            response = await asyncio.to_thread(
                client.search,
                query=query,
                include_answer="advanced",
                search_depth="advanced",
            )

            if not response or not isinstance(response, dict):
                raise ValueError("Invalid response payload from Tavily API.")

            answer = response.get("answer")
            if not answer:
                raise ValueError("Tavily response is missing the 'answer' field.")

            return str(answer)

        except Exception as e:
            return format_error("tavily", str(e))
