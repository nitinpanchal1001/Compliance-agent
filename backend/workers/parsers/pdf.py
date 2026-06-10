"""Extract text from a PDF using pypdf."""

import io

from pypdf import PdfReader


def parse(raw: bytes) -> tuple[str, int]:
    """Returns (text, page_count)."""
    reader = PdfReader(io.BytesIO(raw))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip(), len(reader.pages)
