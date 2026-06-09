import os
import pytest
from unittest.mock import patch
from mcp_web_search.config import Config


@patch("mcp_web_search.config.load_dotenv")
def test_config_defaults_log_level(mock_load_dotenv) -> None:
    # Arrange
    env_mock = {
        "TAVILY_API_KEY": "test-tavily-key",
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-openai-key",
    }
    
    # Act
    with patch.dict(os.environ, env_mock, clear=True):
        config = Config.from_env()
        
    # Assert
    assert config.LOG_LEVEL == "INFO"


@patch("mcp_web_search.config.load_dotenv")
def test_config_parses_custom_log_level(mock_load_dotenv) -> None:
    # Arrange
    env_mock = {
        "TAVILY_API_KEY": "test-tavily-key",
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-openai-key",
        "LOG_LEVEL": "debug",
    }
    
    # Act
    with patch.dict(os.environ, env_mock, clear=True):
        config = Config.from_env()
        
    # Assert
    assert config.LOG_LEVEL == "DEBUG"


@patch("mcp_web_search.config.load_dotenv")
def test_config_rejects_invalid_log_level(mock_load_dotenv) -> None:
    # Arrange
    env_mock = {
        "TAVILY_API_KEY": "test-tavily-key",
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-openai-key",
        "LOG_LEVEL": "invalid-level",
    }
    
    # Act & Assert
    with patch.dict(os.environ, env_mock, clear=True):
        with pytest.raises(ValueError, match="Configuration error: LOG_LEVEL must be one of"):
            Config.from_env()


@patch("mcp_web_search.config.load_dotenv")
def test_config_default_summarization_model_is_gpt_5_mini(mock_load_dotenv) -> None:
    env_mock = {
        "TAVILY_API_KEY": "test-tavily-key",
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-openai-key",
    }
    with patch.dict(os.environ, env_mock, clear=True):
        config = Config.from_env()
    assert config.SUMMARIZATION_MODEL == "gpt-5-mini"
    assert config.MCP_HTTP_PORT == 8000


@patch("mcp_web_search.config.load_dotenv")
def test_config_rejects_unsupported_provider(mock_load_dotenv) -> None:
    env_mock = {
        "TAVILY_API_KEY": "test-tavily-key",
        "LLM_PROVIDER": "anthropic",
        "OPENAI_API_KEY": "test-openai-key",
    }
    with patch.dict(os.environ, env_mock, clear=True):
        with pytest.raises(ValueError, match="LLM_PROVIDER 'anthropic' is not supported"):
            Config.from_env()


@patch("mcp_web_search.config.load_dotenv")
def test_config_rejects_unsupported_summarization_model(mock_load_dotenv) -> None:
    env_mock = {
        "TAVILY_API_KEY": "test-tavily-key",
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-openai-key",
        "SUMMARIZATION_MODEL": "not-a-real-model",
    }
    with patch.dict(os.environ, env_mock, clear=True):
        with pytest.raises(ValueError, match="SUMMARIZATION_MODEL 'not-a-real-model' is not a supported"):
            Config.from_env()


@patch("mcp_web_search.config.load_dotenv")
def test_config_rejects_unsupported_embedding_model(mock_load_dotenv) -> None:
    env_mock = {
        "TAVILY_API_KEY": "test-tavily-key",
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-openai-key",
        "EMBEDDING_MODEL": "not-a-real-embedding",
    }
    with patch.dict(os.environ, env_mock, clear=True):
        with pytest.raises(ValueError, match="EMBEDDING_MODEL 'not-a-real-embedding' is not a supported"):
            Config.from_env()
