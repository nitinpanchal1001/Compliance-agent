"""Parse an .eml email into a flat text transcript (headers + body)."""

from email import message_from_bytes
from email.policy import default


def parse(raw: bytes) -> str:
    msg = message_from_bytes(raw, policy=default)

    headers = [
        f"From: {msg.get('from', '')}",
        f"To: {msg.get('to', '')}",
        f"Date: {msg.get('date', '')}",
        f"Subject: {msg.get('subject', '')}",
    ]

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
        else:
            # fall back to the first text/html part stripped of tags is overkill;
            # just take any text payload we can find.
            for part in msg.walk():
                if part.get_content_maintype() == "text":
                    body = part.get_content()
                    break
    else:
        body = msg.get_content()

    return "\n".join(headers) + "\n\n" + (body or "").strip()
