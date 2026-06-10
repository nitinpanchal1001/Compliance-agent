"""Decode plain text / markdown."""


def parse(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace").strip()
