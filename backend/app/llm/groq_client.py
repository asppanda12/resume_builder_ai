"""Groq implementation of LLMClient. Select with LLM_PROVIDER=groq.

Groq exposes an OpenAI-compatible Chat Completions API with free tier models that support
JSON mode. GROQ_MODEL accepts any model slug listed on console.groq.com/keys (e.g. mixtral-8x7b-32768).
"""
import json
import re

import openai
from pydantic import ValidationError

from app.llm.base import LLMClient, LLMError, T

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


class GroqClient(LLMClient):
    def __init__(self, *, api_key: str, model: str):
        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=GROQ_BASE_URL,
        )
        self._model = model

    async def generate(self, *, system: str, prompt: str, output_model: type[T]) -> T:
        schema = output_model.model_json_schema()
        try:
            completion = await self._create(
                system,
                prompt,
                {"type": "json_schema", "json_schema": {"name": output_model.__name__, "strict": False, "schema": schema}},
            )
        except _NoJsonSupportError:
            # Fallback to JSON mode with schema in the system prompt.
            completion = await self._create(
                f"{system}\n\nRespond with a single JSON object that conforms to this JSON Schema:\n{json.dumps(schema)}",
                prompt,
                {"type": "json_object"},
            )

        if not completion.choices:
            raise LLMError("Groq returned an empty response.")
        choice = completion.choices[0]
        if choice.finish_reason == "length":
            raise LLMError("The model's response was cut off. Try a shorter resume or job description.")
        content = _CODE_FENCE.sub("", (choice.message.content or "").strip())
        try:
            return output_model.model_validate_json(content)
        except ValidationError as exc:
            raise LLMError(
                f"{self._model} returned output that doesn't match the expected schema. "
                "Try a model that supports structured outputs."
            ) from exc

    async def _create(self, system: str, prompt: str, response_format: dict):
        try:
            return await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                response_format=response_format,
            )
        except openai.AuthenticationError as exc:
            raise LLMError("Groq rejected the API key. Check GROQ_API_KEY.") from exc
        except openai.RateLimitError as exc:
            raise LLMError("Groq rate limit reached. Wait a minute and try again.") from exc
        except openai.NotFoundError as exc:
            if "does not support" in exc.message or "not supported" in exc.message:
                raise _NoJsonSupportError(str(exc)) from exc
            raise LLMError(f"Groq error: {exc.message}") from exc
        except openai.APIStatusError as exc:
            # json_validate_failed means json_schema isn't supported; fall back to json_object mode.
            if "json_validate_failed" in exc.message or "json_validate" in exc.message:
                raise _NoJsonSupportError(str(exc)) from exc
            raise LLMError(f"Groq error ({exc.status_code}): {exc.message}") from exc
        except openai.APIConnectionError as exc:
            raise LLMError("Could not reach Groq. Check your network connection.") from exc


class _NoJsonSupportError(LLMError):
    """Groq model doesn't support the requested JSON format."""
