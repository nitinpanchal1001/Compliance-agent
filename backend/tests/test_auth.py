"""Auth, token rotation, and revocation."""

import pytest
from conftest import auth_headers, make_tenant

pytestmark = pytest.mark.asyncio


async def test_signup_login_me(client):
    token, email, _ = await make_tenant(client)
    r = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == email
    assert body["role"] == "admin"


async def test_wrong_password(client):
    _, email, _ = await make_tenant(client)
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "nope"})
    assert r.status_code == 401


async def test_invalid_email_rejected(client):
    r = await client.post(
        "/api/v1/tenants",
        json={"name": "X", "slug": "bad-email-org", "admin_email": "garbage", "admin_password": "password123"},
    )
    assert r.status_code == 422


async def test_refresh_rotation_and_reuse(client):
    _, email, _ = await make_tenant(client)
    login = (await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})).json()
    r1 = login["refresh_token"]

    rotated = await client.post("/api/v1/auth/refresh", json={"refresh_token": r1})
    assert rotated.status_code == 200
    r2 = rotated.json()["refresh_token"]
    assert r2 and r2 != r1

    # Old token is now dead.
    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": r1})
    assert reused.status_code == 401


async def test_logout_revokes(client):
    _, email, _ = await make_tenant(client)
    login = (await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})).json()
    refresh = login["refresh_token"]

    assert (await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})).status_code == 204
    after = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert after.status_code == 401


async def test_unauthenticated_rejected(client):
    assert (await client.get("/api/v1/auth/me")).status_code in (401, 403)
    assert (await client.get("/api/v1/auth/me", headers=auth_headers("garbage"))).status_code == 401
