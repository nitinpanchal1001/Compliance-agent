"""Transcribe audio to text via OpenAI Whisper (whisper-1)."""

import io
from functools import lru_cache

from openai import OpenAI

from core.config import get_settings

settings = get_settings()


@lru_cache
def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def parse(raw: bytes, filename: str = "audio.mp3") -> str:
    buffer = io.BytesIO(raw)
    # OpenAI's SDK uses the file's name to infer format; give it a sane default.
    buffer.name = filename or "audio.mp3"
    resp = _client().audio.transcriptions.create(
        model=settings.openai_whisper_model, file=buffer
    )
    return resp.text.strip()
