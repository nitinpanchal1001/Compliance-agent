"""Dispatch raw file bytes to the right parser based on DocumentFileType.

Returns (text, page_count). page_count is only meaningful for PDFs; otherwise None.
"""

from db.models.document import DocumentFileType
from workers.parsers import audio, email_parser, pdf, slack, text


def extract_text(
    file_type: DocumentFileType, raw: bytes, filename: str
) -> tuple[str, int | None]:
    if file_type == DocumentFileType.pdf:
        return pdf.parse(raw)
    if file_type == DocumentFileType.email:
        return email_parser.parse(raw), None
    if file_type == DocumentFileType.slack:
        return slack.parse(raw), None
    if file_type == DocumentFileType.audio:
        return audio.parse(raw, filename), None
    if file_type in (DocumentFileType.text, DocumentFileType.other):
        return text.parse(raw), None
    raise ValueError(f"Unsupported file type: {file_type}")
