"""Application settings, read from environment variables (and .env when present)."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Running locally from backend/ picks up the repo-root .env; docker-compose
    # injects the same variables directly.
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017/resume_builder"

    llm_provider: Literal["anthropic", "openai", "openrouter", "groq", "ollama"] = "anthropic"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-5"
    openai_api_key: str | None = None
    openai_model: str | None = None
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None
    groq_api_key: str | None = None
    groq_model: str | None = None
    # docker-compose sets OLLAMA_BASE_URL to host.docker.internal so the container reaches the Mac.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_num_ctx: int = Field(16384, ge=2048)

    # "local" = dependency-free term-vector cosine; "openai" = OpenAI embeddings API.
    embeddings_provider: Literal["local", "openai"] = "local"
    openai_embedding_model: str = "text-embedding-3-small"

    ats_threshold: float = Field(90, ge=0, le=100)
    optimize_mode: Literal["improve", "gate"] = "improve"
    max_optimize_iterations: int = Field(3, ge=1, le=10)
    ats_keyword_weight: float = Field(0.7, ge=0)
    ats_semantic_weight: float = Field(0.3, ge=0)
    # Raw cosine similarity is mapped linearly from [floor, ceiling] onto 0-100.
    # Leave unset to use the provider defaults in services/similarity.py.
    ats_semantic_floor: float | None = None
    ats_semantic_ceiling: float | None = None

    gmail_address: str | None = None
    gmail_app_password: str | None = None

    @model_validator(mode="after")
    def _check(self) -> "Settings":
        if self.ats_keyword_weight + self.ats_semantic_weight <= 0:
            raise ValueError("ATS_KEYWORD_WEIGHT and ATS_SEMANTIC_WEIGHT cannot both be 0")
        if (
            self.ats_semantic_floor is not None
            and self.ats_semantic_ceiling is not None
            and self.ats_semantic_ceiling <= self.ats_semantic_floor
        ):
            raise ValueError("ATS_SEMANTIC_CEILING must be greater than ATS_SEMANTIC_FLOOR")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
