"""Pure unit tests — no DB or HTTP."""

from types import SimpleNamespace

import pytest

from agents import risk_scoring
from core import security
from core.validators import _validate_email
from workers.chunking import chunk_text


def _v(severity, confidence, ref="GDPR Art. 5"):
    return SimpleNamespace(severity=severity, confidence=confidence, policy_ref=ref)


def test_risk_scoring_empty_is_low():
    a = risk_scoring.assess([])
    assert a.score == 0
    assert a.tier == "low"


def test_risk_scoring_caps_at_100():
    a = risk_scoring.assess([_v("critical", 1.0) for _ in range(5)])
    assert a.score == 100
    assert a.tier == "critical"


def test_risk_scoring_tiers():
    assert risk_scoring.assess([_v("high", 1.0)]).tier == "medium"  # 25 pts -> medium
    assert risk_scoring.assess([_v("low", 1.0)]).tier == "low"  # 5 pts -> low
    a = risk_scoring.assess([_v("critical", 1.0), _v("high", 1.0)])
    assert a.score == 65  # 40 + 25
    assert a.tier == "high"


def test_risk_scoring_dismissed_excluded_by_caller():
    # assess scores whatever it's given; the API filters dismissed before calling.
    a = risk_scoring.assess([_v("critical", 1.0)])
    assert a.score == 40
    assert a.breakdown["violation_count"] == 1


def test_chunking_short_text_single_chunk():
    assert chunk_text("hello world") == ["hello world"]


def test_chunking_long_text_splits_with_overlap():
    text = "word " * 600  # ~3000 chars
    chunks = chunk_text(text, size=1000, overlap=150)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)


def test_email_accepts_internal_domain():
    assert _validate_email("Admin@Acme.LOCAL") == "admin@acme.local"


@pytest.mark.parametrize("bad", ["not-an-email", "a@b", "@x.com", "x@", ""])
def test_email_rejects_garbage(bad):
    with pytest.raises(ValueError):
        _validate_email(bad)


def test_password_hash_roundtrip():
    h = security.hash_password("s3cret-pass")
    assert h != "s3cret-pass"
    assert security.verify_password("s3cret-pass", h)
    assert not security.verify_password("wrong", h)


def test_token_create_and_decode():
    access = security.create_access_token("u1", "t1", "admin")
    payload = security.decode_token(access)
    assert payload["sub"] == "u1"
    assert payload["type"] == "access"
    assert payload["role"] == "admin"

    refresh, jti = security.create_refresh_token("u1", "t1")
    rp = security.decode_token(refresh)
    assert rp["type"] == "refresh"
    assert rp["jti"] == jti
