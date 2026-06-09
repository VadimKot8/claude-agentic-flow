from openai import AsyncOpenAI
from mcp_web_search.llm.base import ChatLLM, Embeddings


class OpenAIChatLLM(ChatLLM):
    """OpenAI Chat LLM provider."""

    def __init__(self, api_key: str, model_name: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model_name = model_name

    async def complete(self, system: str, user: str) -> str:
        """Complete a chat prompt using system and user messages."""
        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content
        if content is None:
            return ""
        return content


class OpenAIEmbeddings(Embeddings):
    """OpenAI Embeddings provider."""

    def __init__(self, api_key: str, model_name: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model_name = model_name

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vector representations."""
        response = await self._client.embeddings.create(
            input=texts,
            model=self._model_name,
        )
        return [item.embedding for item in response.data]
