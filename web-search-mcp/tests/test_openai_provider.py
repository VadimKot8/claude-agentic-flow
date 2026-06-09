from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from openai import OpenAIError
from mcp_web_search.llm.openai_provider import OpenAIChatLLM, OpenAIEmbeddings
from mcp_web_search.llm.base import ChatLLM, Embeddings


@pytest.mark.asyncio
async def test_openai_chat_llm_complete() -> None:
    api_key = "test-api-key"
    model_name = "test-model"

    with patch("mcp_web_search.llm.openai_provider.AsyncOpenAI") as mock_async_openai:
        # Set up mock client and response
        mock_client = MagicMock()
        mock_async_openai.return_value = mock_client

        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Summary of web page"
        mock_completion.choices = [mock_choice]

        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        chat = OpenAIChatLLM(api_key=api_key, model_name=model_name)

        # Verify that AsyncOpenAI was initialized with the api_key
        mock_async_openai.assert_called_once_with(api_key=api_key)

        result = await chat.complete(system="System prompt", user="User prompt")

        assert result == "Summary of web page"
        mock_client.chat.completions.create.assert_called_once_with(
            model=model_name,
            messages=[
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "User prompt"},
            ],
        )


@pytest.mark.asyncio
async def test_openai_chat_llm_complete_none_content() -> None:
    api_key = "test-api-key"
    model_name = "test-model"

    with patch("mcp_web_search.llm.openai_provider.AsyncOpenAI") as mock_async_openai:
        mock_client = MagicMock()
        mock_async_openai.return_value = mock_client

        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_completion.choices = [mock_choice]

        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        chat = OpenAIChatLLM(api_key=api_key, model_name=model_name)
        result = await chat.complete(system="System prompt", user="User prompt")

        assert result == ""


@pytest.mark.asyncio
async def test_openai_chat_llm_exception() -> None:
    api_key = "test-api-key"
    model_name = "test-model"

    with patch("mcp_web_search.llm.openai_provider.AsyncOpenAI") as mock_async_openai:
        mock_client = MagicMock()
        mock_async_openai.return_value = mock_client

        mock_client.chat.completions.create = AsyncMock(
            side_effect=OpenAIError("API Error")
        )

        chat = OpenAIChatLLM(api_key=api_key, model_name=model_name)

        with pytest.raises(OpenAIError, match="API Error"):
            await chat.complete(system="System prompt", user="User prompt")


@pytest.mark.asyncio
async def test_openai_embeddings_embed() -> None:
    api_key = "test-api-key"
    model_name = "test-model"

    with patch("mcp_web_search.llm.openai_provider.AsyncOpenAI") as mock_async_openai:
        mock_client = MagicMock()
        mock_async_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_data_1 = MagicMock()
        mock_data_1.embedding = [0.1, 0.2]
        mock_data_2 = MagicMock()
        mock_data_2.embedding = [0.3, 0.4]
        mock_response.data = [mock_data_1, mock_data_2]

        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        embeddings = OpenAIEmbeddings(api_key=api_key, model_name=model_name)

        # Verify that AsyncOpenAI was initialized with the api_key
        mock_async_openai.assert_called_once_with(api_key=api_key)

        result = await embeddings.embed(["text1", "text2"])

        assert result == [[0.1, 0.2], [0.3, 0.4]]
        mock_client.embeddings.create.assert_called_once_with(
            input=["text1", "text2"], model=model_name
        )


@pytest.mark.asyncio
async def test_openai_embeddings_exception() -> None:
    api_key = "test-api-key"
    model_name = "test-model"

    with patch("mcp_web_search.llm.openai_provider.AsyncOpenAI") as mock_async_openai:
        mock_client = MagicMock()
        mock_async_openai.return_value = mock_client

        mock_client.embeddings.create = AsyncMock(
            side_effect=OpenAIError("Embedding Error")
        )

        embeddings = OpenAIEmbeddings(api_key=api_key, model_name=model_name)

        with pytest.raises(OpenAIError, match="Embedding Error"):
            await embeddings.embed(["text1", "text2"])


def test_implements_protocols() -> None:
    with patch("mcp_web_search.llm.openai_provider.AsyncOpenAI"):
        chat = OpenAIChatLLM(api_key="key", model_name="model")
        embeddings = OpenAIEmbeddings(api_key="key", model_name="model")

        assert isinstance(chat, ChatLLM)
        assert isinstance(embeddings, Embeddings)
