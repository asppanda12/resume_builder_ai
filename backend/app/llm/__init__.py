"""LLM provider factory. Select with LLM_PROVIDER=anthropic|openai|openrouter|groq|ollama."""
from functools import lru_cache

from app.config import get_settings
from app.llm.base import LLMClient, LLMError, LLMNotConfiguredError

__all__ = ["LLMClient", "LLMError", "LLMNotConfiguredError", "get_llm"]


@lru_cache
def get_llm() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider == "ollama":
        from app.llm.ollama_client import OllamaClient

        return OllamaClient(
            base_url=settings.ollama_base_url, model=settings.ollama_model, num_ctx=settings.ollama_num_ctx
        )

    if settings.llm_provider == "groq":
        if not (settings.groq_api_key and settings.groq_model):
            raise LLMNotConfiguredError("Set GROQ_API_KEY and GROQ_MODEL to use the Groq provider.")
        from app.llm.groq_client import GroqClient

        return GroqClient(api_key=settings.groq_api_key, model=settings.groq_model)

    if settings.llm_provider == "openrouter":
        if not (settings.openrouter_api_key and settings.openrouter_model):
            raise LLMNotConfiguredError("Set OPENROUTER_API_KEY and OPENROUTER_MODEL to use the OpenRouter provider.")
        from app.llm.openrouter_client import OpenRouterClient

        return OpenRouterClient(api_key=settings.openrouter_api_key, model=settings.openrouter_model)

    if settings.llm_provider == "openai":
        if not (settings.openai_api_key and settings.openai_model):
            raise LLMNotConfiguredError("Set OPENAI_API_KEY and OPENAI_MODEL to use the OpenAI provider.")
        from app.llm.openai_client import OpenAIClient

        return OpenAIClient(api_key=settings.openai_api_key, model=settings.openai_model)

    if not settings.anthropic_api_key:
        raise LLMNotConfiguredError("Set ANTHROPIC_API_KEY in .env to enable the AI features.")
    from app.llm.anthropic_client import AnthropicClient

    return AnthropicClient(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
