"""Human review: per-violation decisions, risk recompute, case closure, audit."""

import pytest
from conftest import auth_headers, make_tenant

from db.models.case import Case, CaseStatus, RiskTier
from db.models.document import Document, DocumentFileType, DocumentStatus
from db.models.violation import Violation, ViolationSeverity

pytestmark = pytest.mark.asyncio


async def _seed_case(session, tenant_id, user_id):
    doc = Document(
        tenant_id=tenant_id,
        uploaded_by=user_id,
        name="x.txt",
        s3_key="k",
        file_type=DocumentFileType.text,
        status=DocumentStatus.ready,
    )
    session.add(doc)
    await session.flush()
    case = Case(
        tenant_id=tenant_id,
        document_id=doc.id,
        status=CaseStatus.pending_review,
        risk_score=100,
        risk_tier=RiskTier.critical,
    )
    session.add(case)
    await session.flush()
    v1 = Violation(
        case_id=case.id, violation_type="A", severity=ViolationSeverity.critical,
        policy_ref="PCI-DSS Req. 3.2", doc_excerpt="x", clause_text="c", reasoning="r", confidence=1.0,
    )
    v2 = Violation(
        case_id=case.id, violation_type="B", severity=ViolationSeverity.high,
        policy_ref="GDPR Art. 5", doc_excerpt="y", clause_text="c", reasoning="r", confidence=1.0,
    )
    session.add_all([v1, v2])
    await session.commit()
    return case.id, v1.id, v2.id


async def test_review_recompute_and_close(client, session):
    admin, _, _ = await make_tenant(client)
    me = (await client.get("/api/v1/auth/me", headers=auth_headers(admin))).json()
    cid, vid1, vid2 = await _seed_case(session, me["tenant_id"], me["id"])

    # Dismiss the critical → re-score from the surviving high; tier drops to "high"
    # (worst remaining severity). Case stays open while a violation is unreviewed.
    r = await client.post(
        f"/api/v1/cases/{cid}/violations/{vid1}/review",
        headers=auth_headers(admin),
        json={"decision": "dismissed", "note": "false positive"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending_review"
    assert body["risk_tier"] == "high"
    assert 50 <= body["risk_score"] <= 74

    # Confirm the last one → fully adjudicated → closed.
    r = await client.post(
        f"/api/v1/cases/{cid}/violations/{vid2}/review",
        headers=auth_headers(admin),
        json={"decision": "confirmed"},
    )
    assert r.json()["status"] == "closed"

    # Review trail records both decisions.
    reviews = (await client.get(f"/api/v1/cases/{cid}/reviews", headers=auth_headers(admin))).json()
    decisions = sorted(rv["decision"] for rv in reviews)
    assert decisions == ["confirmed", "dismissed"]


async def test_review_requires_reviewer_role(client, session):
    admin, _, _ = await make_tenant(client)
    me = (await client.get("/api/v1/auth/me", headers=auth_headers(admin))).json()
    cid, vid1, _ = await _seed_case(session, me["tenant_id"], me["id"])

    # make a viewer
    await client.post(
        "/api/v1/users",
        headers=auth_headers(admin),
        json={"email": "v-review@acme.com", "password": "password123", "role": "viewer"},
    )
    vt = (await client.post("/api/v1/auth/login", json={"email": "v-review@acme.com", "password": "password123"})).json()["access_token"]

    r = await client.post(
        f"/api/v1/cases/{cid}/violations/{vid1}/review",
        headers=auth_headers(vt),
        json={"decision": "confirmed"},
    )
    assert r.status_code == 403
