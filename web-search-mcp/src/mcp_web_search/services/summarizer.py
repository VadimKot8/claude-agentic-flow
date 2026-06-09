from mcp_web_search.llm.base import ChatLLM


class Summarizer:
    """
    Summarizer class handles simplification of search queries using an LLM.
    Used by the background search/indexing processes to compress/simplify verbose 
    or noisy queries before performing database searches/indexing.
    """

    def __init__(self, llm: ChatLLM) -> None:
        """
        Initialize the Summarizer service with a ChatLLM instance.
        """
        self.llm = llm

    async def simplify(self, raw_query: str) -> str:
        """
        Simplifies the raw query into a single short, context-preserving phrase.
        Strips stack traces, log noise, error codes, and conversational filler words,
        retaining only the key technical intent.
        
        Args:
            raw_query: The verbose or noisy query to simplify.
            
        Returns:
            A simplified search query phrase.
        """
        if not raw_query or not raw_query.strip():
            return ""

        system_prompt = (
            "You are a search query summarizer. Your task is to rewrite the user's input "
            "into a single short, context-preserving search phrase. "
            "Strip out all stack traces, log noise, raw error dumps, and conversational filler words. "
            "Retain only the core technical intent. "
            "Output ONLY the rewritten search phrase, with no preamble, no markdown formatting, "
            "and no additional explanation."
        )

        result = await self.llm.complete(system=system_prompt, user=raw_query.strip())
        return result.strip().strip('"\'')
