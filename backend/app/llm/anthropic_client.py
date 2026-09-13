"""Claude implementation of LLMClient (official Anthropic Python SDK)."""
import anthropic

from app.llm.base import LLMClient, LLMError, T

# Server-side refusal fallback: if the primary model declines, the API re-runs the
# request on a fallback model inside the same call. Only sent for models that support it.
_FALLBACK_BETA = "server-side-fallback-2026-07-01"
_FALLBACK_MODELS = {"claude-opus-5", "claude-fable-5-1"}


class AnthropicClient(LLMClient):
    def __init__(self, *, api_key: str, model: str):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def generate(self, *, system: str, prompt: str, output_model: type[T]) -> T:
        extra = (
            {"betas": [_FALLBACK_BETA], "fallbacks": "default"}
            if self._model in _FALLBACK_MODELS
            else {}
        )
        try:
            response = await self._client.beta.messages.parse(
                model=self._model,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_format=output_model,
                **extra,
            )
        except anthropic.AuthenticationError as exc:
            raise LLMError("Claude rejected the API key. Check ANTHROPIC_API_KEY.") from exc
        except anthropic.RateLimitError as exc:
            raise LLMError("Claude rate limit reached. Wait a minute and try again.") from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Claude API error ({exc.status_code}): {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError("Could not reach the Claude API. Check your network connection.") from exc

        if response.stop_reason == "refusal":
            raise LLMError("Claude declined to process this request.")
        if response.stop_reason == "max_tokens":
            raise LLMError("Claude's response was cut off. Try a shorter resume or job description.")
        if response.parsed_output is None:
            raise LLMError("Claude returned no structured output.")
        return response.parsed_output
