"""Semantic similarity between resume and job description, on a 0-100 scale.

Assumption: Anthropic has no embeddings endpoint and sentence-transformers would add
~2 GB of torch to the image, so the default is a dependency-free term-vector cosine.
Set EMBEDDINGS_PROVIDER=openai for true embedding similarity.
"""
import math
import re
from collections import Counter

import openai

from app.config import get_settings
from app.llm.base import LLMError, LLMNotConfiguredError

# Raw cosine ranges differ by method, so each one maps its own [floor, ceiling] onto 0-100.
# Defaults are calibrated for typical resume/JD pairs; override with ATS_SEMANTIC_FLOOR/_CEILING.
_DEFAULT_RANGE = {"local": (0.05, 0.45), "openai": (0.20, 0.70)}

_STOPWORDS = frozenset(
    """a about above after again all also am an and any are as at be because been before being
    below between both but by can could did do does doing down during each etc few for from
    further had has have having he her here hers him his how i if in into is it its itself just
    me more most my no nor not now of off on once only or other our ours out over own per same
    she should so some such than that the their theirs them then there these they this those
    through to too under until up us very via was we were what when where which while who whom
    why will with within without would you your yours ability able work working team strong
    excellent knowledge skills skill years year role responsibilities including using use""".split()
)
# Keeps tech tokens such as c++, c#, node.js and ci/cd pieces intact.
_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#.]*[a-z0-9+#]|[a-z0-9]")


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if len(t) > 1 and t not in _STOPWORDS]


def _cosine(a: dict[str, float] | list[float], b: dict[str, float] | list[float]) -> float:
    if isinstance(a, dict):
        dot = sum(w * b.get(t, 0.0) for t, w in a.items())
        norm_a, norm_b = math.sqrt(sum(w * w for w in a.values())), math.sqrt(sum(w * w for w in b.values()))
    else:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a, norm_b = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _local_cosine(a: str, b: str) -> float:
    # Sub-linear term frequency so a few repeated words don't dominate.
    vec_a = {t: 1 + math.log(c) for t, c in Counter(_tokens(a)).items()}
    vec_b = {t: 1 + math.log(c) for t, c in Counter(_tokens(b)).items()}
    return _cosine(vec_a, vec_b)


async def _openai_cosine(a: str, b: str) -> float:
    settings = get_settings()
    if not settings.openai_api_key:
        raise LLMNotConfiguredError("EMBEDDINGS_PROVIDER=openai requires OPENAI_API_KEY.")
    try:
        async with openai.AsyncOpenAI(api_key=settings.openai_api_key) as client:
            response = await client.embeddings.create(model=settings.openai_embedding_model, input=[a, b])
    except openai.OpenAIError as exc:
        raise LLMError(f"Embedding request failed: {exc}") from exc
    return _cosine(response.data[0].embedding, response.data[1].embedding)


async def semantic_score(resume_text: str, jd_text: str) -> float:
    settings = get_settings()
    provider = settings.embeddings_provider
    raw = await _openai_cosine(resume_text, jd_text) if provider == "openai" else _local_cosine(resume_text, jd_text)

    floor, ceiling = _DEFAULT_RANGE[provider]
    if settings.ats_semantic_floor is not None:
        floor = settings.ats_semantic_floor
    if settings.ats_semantic_ceiling is not None:
        ceiling = settings.ats_semantic_ceiling
    scaled = (raw - floor) / (ceiling - floor)
    return round(100 * min(1.0, max(0.0, scaled)), 1)
