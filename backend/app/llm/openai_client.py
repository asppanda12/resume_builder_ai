"""OpenAI implementation of LLMClient. Select with LLM_PROVIDER=openai."""
import json

import openai
from pydantic import ValidationError

from app.llm.base import LLMClient, LLMError, T


class OpenAIClient(LLMClient):
    def __init__(self, *, api_key: str, model: str):
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate(self, *, system: str, prompt: str, output_model: type[T]) -> T:
        # Non-strict JSON schema: OpenAI's strict mode rejects optional/defaulted fields,
        # which the resume schema relies on. Pydantic validates the result instead.
        text_format = {
            "format": {
                "type": "json_schema",
                "name": output_model.__name__,
                "schema": output_model.model_json_schema(),
                "strict": False,
            }
        }
        try:
            response = await self._client.responses.create(
                model=self._model, instructions=system, input=prompt, text=text_format
            )
        except openai.AuthenticationError as exc:
            raise LLMError("OpenAI rejected the API key. Check OPENAI_API_KEY.") from exc
        except openai.RateLimitError as exc:
            raise LLMError("OpenAI rate limit reached. Wait a minute and try again.") from exc
        except openai.APIStatusError as exc:
            raise LLMError(f"OpenAI API error ({exc.status_code}): {exc.message}") from exc
        except openai.APIConnectionError as exc:
            raise LLMError("Could not reach the OpenAI API. Check your network connection.") from exc

        try:
            return output_model.model_validate_json(response.output_text)
        except (ValidationError, json.JSONDecodeError) as exc:
            raise LLMError("OpenAI returned output that doesn't match the expected schema.") from exc
