"""Provider-neutral LLM interface. The rest of the app talks only to LLMClient."""
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """The LLM call failed or returned nothing usable."""


class LLMNotConfiguredError(LLMError):
    """No credentials are configured for the selected provider."""


class LLMClient(ABC):
    @abstractmethod
    async def generate(self, *, system: str, prompt: str, output_model: type[T]) -> T:
        """Run one request and return the answer validated as `output_model`."""
