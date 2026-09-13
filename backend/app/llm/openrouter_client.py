"""OpenRouter implementation of LLMClient. Select with LLM_PROVIDER=openrouter.

OpenRouter exposes an OpenAI-compatible Chat Completions API, so this reuses the openai SDK
with OpenRouter's base URL. OPENROUTER_MODEL accepts any model slug listed on openrouter.ai/models.
"""
import json
import re

import openai
from pydantic import ValidationError

from app.llm.base import LLMClient, LLMError, T

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


class OpenRouterClient(LLMClient):
    def __init__(self, *, api_key: str, model: str):
        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers={"X-Title": "AI Resume Builder"},  # optional app attribution on openrouter.ai
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
        except _NoCompatibleEndpointError:
            # Many models (e.g. most :free variants) support JSON mode but not json_schema structured
            # outputs, so fall back to JSON mode with the schema spelled out in the system prompt.
            completion = await self._create(
                f"{system}\n\nRespond with a single JSON object that conforms to this JSON Schema:\n{json.dumps(schema)}",
                prompt,
                {"type": "json_object"},
            )

        if not completion.choices:
            raise LLMError("OpenRouter returned an empty response.")
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
                # Route only to upstream providers that honour response_format, so we always get JSON back.
                extra_body={"provider": {"require_parameters": True}},
            )
        except openai.AuthenticationError as exc:
            raise LLMError("OpenRouter rejected the API key. Check OPENROUTER_API_KEY.") from exc
        except openai.RateLimitError as exc:
            raise LLMError("OpenRouter rate limit reached. Wait a minute and try again.") from exc
        except openai.NotFoundError as exc:
            if "No endpoints found" in exc.message:
                raise _NoCompatibleEndpointError(
                    f"No OpenRouter provider for {self._model} supports JSON output. "
                    "Pick a model that supports structured outputs."
                ) from exc
            raise LLMError(f"OpenRouter error ({exc.status_code}): {exc.message}") from exc
        except openai.APIStatusError as exc:
            raise LLMError(f"OpenRouter error ({exc.status_code}): {exc.message}") from exc
        except openai.APIConnectionError as exc:
            raise LLMError("Could not reach OpenRouter. Check your network connection.") from exc


class _NoCompatibleEndpointError(LLMError):
    """OpenRouter found no upstream endpoint that supports every requested parameter."""
