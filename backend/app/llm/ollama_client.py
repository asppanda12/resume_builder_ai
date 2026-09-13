"""Local Ollama implementation of LLMClient. Select with LLM_PROVIDER=ollama.

Uses Ollama's native /api/chat endpoint instead of its OpenAI-compatible one: only the native
API accepts a JSON schema as `format` (constrained decoding) and a per-request `num_ctx`.
Ollama's default 4096-token context is too small for a resume plus a job description and
silently truncates the prompt.
"""
import httpx2
from pydantic import ValidationError

from app.llm.base import LLMClient, LLMError, T


def _require_all_fields(schema: dict) -> dict:
    """Mark every property required. With optional fields, constrained decoding lets small local
    models skip whole sections (name, experience) instead of filling them in."""
    for node in [schema, *schema.get("$defs", {}).values()]:
        if "properties" in node:
            node["required"] = list(node["properties"])
    return schema


class OllamaClient(LLMClient):
    def __init__(self, *, base_url: str, model: str, num_ctx: int):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._num_ctx = num_ctx

    async def generate(self, *, system: str, prompt: str, output_model: type[T]) -> T:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "format": _require_all_fields(output_model.model_json_schema()),
            "stream": False,
            "options": {"num_ctx": self._num_ctx, "temperature": 0.2},
        }
        try:
            # Generating a whole resume locally can take a minute or more.
            async with httpx2.AsyncClient(timeout=httpx2.Timeout(600.0, connect=5.0)) as client:
                response = await client.post(f"{self._base_url}/api/chat", json=payload)
        except httpx2.ConnectError as exc:
            raise LLMError(
                f"Could not reach Ollama at {self._base_url}. Start it with `brew services start ollama`."
            ) from exc
        except httpx2.TimeoutException as exc:
            raise LLMError("Ollama took too long to respond. Try a smaller model.") from exc

        if response.status_code == 404:
            raise LLMError(f"Ollama model '{self._model}' isn't installed. Run: ollama pull {self._model}")
        if response.is_error:
            detail = response.json().get("error", response.text) if response.content else ""
            raise LLMError(f"Ollama error ({response.status_code}): {str(detail)[:300]}")

        data = response.json()
        if data.get("done_reason") == "length":
            raise LLMError("The model's response was cut off. Raise OLLAMA_NUM_CTX or shorten the input.")
        try:
            return output_model.model_validate_json(data.get("message", {}).get("content", ""))
        except ValidationError as exc:
            raise LLMError(
                f"{self._model} returned output that doesn't match the expected schema. "
                "Try a stronger model such as qwen2.5:7b."
            ) from exc
