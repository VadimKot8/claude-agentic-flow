from mcp_web_search.llm import ChatLLM, Embeddings


class MockChatLLM:
    async def complete(self, system: str, user: str) -> str:
        return f"System: {system}, User: {user}"


class MockEmbeddings:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]


def test_chat_llm_protocol() -> None:
    chat = MockChatLLM()
    assert isinstance(chat, ChatLLM)


def test_embeddings_protocol() -> None:
    embeddings = MockEmbeddings()
    assert isinstance(embeddings, Embeddings)


class NonConformingChatLLM:
    pass


class NonConformingEmbeddings:
    pass


def test_non_conforming_protocols() -> None:
    assert not isinstance(NonConformingChatLLM(), ChatLLM)
    assert not isinstance(NonConformingEmbeddings(), Embeddings)
