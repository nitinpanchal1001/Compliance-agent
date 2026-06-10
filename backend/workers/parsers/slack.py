"""Parse a Slack channel export (JSON) into a readable conversation transcript.

Accepts either a single channel's message array, or an object with a "messages" key.
Each message becomes a "user: text" line, in timestamp order where available.
"""

import json
from datetime import datetime, timezone


def parse(raw: bytes) -> str:
    data = json.loads(raw.decode("utf-8", errors="replace"))

    if isinstance(data, dict):
        messages = data.get("messages", [])
    elif isinstance(data, list):
        messages = data
    else:
        messages = []

    lines: list[str] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        text = (m.get("text") or "").strip()
        if not text:
            continue
        user = m.get("user_profile", {}).get("real_name") or m.get("user") or "unknown"
        ts = m.get("ts")
        when = ""
        if ts:
            try:
                when = datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
            except (ValueError, TypeError):
                when = ""
        prefix = f"[{when}] {user}" if when else user
        lines.append(f"{prefix}: {text}")

    return "\n".join(lines)
