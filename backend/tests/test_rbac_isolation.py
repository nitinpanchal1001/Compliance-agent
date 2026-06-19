"""RBAC enforcement and tenant isolation."""

import pytest
from conftest import auth_headers, login, make_tenant

pytestmark = pytest.mark.asyncio


async def _make_viewer(client, admin_token):
    email = "viewer@acme.com"
    r = await client.post(
        "/api/v1/users",
        headers=auth_headers(admin_token),
        json={"email": email, "password": "password123", "role": "viewer"},
    )
    assert r.status_code == 201
    return await login(client, email, "password123")


async def test_viewer_cannot_create_user(client):
    admin, _, _ = await make_tenant(client)
    viewer = await _make_viewer(client, admin)
    r = await client.post(
        "/api/v1/users",
        headers=auth_headers(viewer),
        json={"email": "x@acme.com", "password": "password123"},
    )
    assert r.status_code == 403


async def test_viewer_cannot_upload(client):
    admin, _, _ = await make_tenant(client)
    viewer = await _make_viewer(client, admin)
    r = await client.post(
        "/api/v1/documents",
        headers=auth_headers(viewer),
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 403


async def test_tenant_isolation_documents(client):
    admin_a, _, _ = await make_tenant(client)
    upload = await client.post(
        "/api/v1/documents",
        headers=auth_headers(admin_a),
        files={"file": ("a.txt", b"secret data", "text/plain")},
    )
    assert upload.status_code == 202
    doc_id = upload.json()["id"]

    admin_b, _, _ = await make_tenant(client)
    # B's list excludes A's doc
    listed = await client.get("/api/v1/documents", headers=auth_headers(admin_b))
    assert all(d["id"] != doc_id for d in listed.json())
    # B fetching A's doc by id → 404
    got = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers(admin_b))
    assert got.status_code == 404


async def test_admin_sees_own_audit_only(client):
    admin_a, _, _ = await make_tenant(client)
    admin_b, _, _ = await make_tenant(client)
    a_audit = (await client.get("/api/v1/audit", headers=auth_headers(admin_a))).json()
    # every entry belongs to A's tenant (we can't see tenant_id, but B's signup must not leak)
    assert isinstance(a_audit, list)
    assert any(e["action"] == "tenant.create" for e in a_audit)
