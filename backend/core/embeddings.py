"""Text → vector embeddings via OpenAI (text-embedding-3-small, 1536 dims)."""

from functools import lru_cache

from openai import OpenAI

from core.config import get_settings

settings = get_settings()

# OpenAI accepts large batches, but cap per-request to stay well under limits.
_BATCH_SIZE = 100


@lru_cache
def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, preserving order. Batches internally."""
    if not texts:
        return []
    vectors: list[list[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        resp = _client().embeddings.create(
            model=settings.openai_embedding_model, input=batch
        )
        vectors.extend(item.embedding for item in resp.data)
    return vectors


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
