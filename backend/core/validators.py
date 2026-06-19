"""Shared field validators.

`Email` is a lenient email type: it accepts any syntactically valid address —
including internal/company domains (e.g. acme.local, corp.internal) — which the
strict `pydantic.EmailStr` rejects as "special-use or reserved". For an internal
compliance tool where users onboard with corporate emails, that strictness blocks
sign-up, so we validate shape only and normalize to lowercase.
"""

import re
from typing import Annotated

from pydantic import AfterValidator

# local-part@domain.tld — pragmatic, not RFC-exhaustive, but accepts real-world
# and internal addresses while rejecting obvious garbage.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    value = value.strip()
    if not _EMAIL_RE.match(value):
        raise ValueError("Enter a valid email address")
    return value.lower()


Email = Annotated[str, AfterValidator(_validate_email)]
