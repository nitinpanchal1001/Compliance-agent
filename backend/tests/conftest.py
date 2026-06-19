"""Test harness.

Spins up an isolated `compliance_test` database, points the app's get_db at it,
disables rate limiting, and stubs external side-effects (S3, Celery enqueues) so
the API can be exercised hermetically. Redis is used for real (token store).
"""

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import core.ratelimit
import db.models  # noqa: F401 — register all mappers
import main
from core.config import get_settings
from db.base import Base, get_db

settings = get_settings()

_TEST_DB = "compliance_test"
_BASE = settings.database_url.rsplit("/", 1)[0]
_TEST_URL = f"{_BASE}/{_TEST_DB}"


@pytest_asyncio.fixture
async def engine():
    # Create the test database (connect to the maintenance 'postgres' db first).
    server_dsn = settings.database_url.replace("+asyncpg", "").rsplit("/", 1)[0] + "/postgres"
    conn = await asyncpg.connect(server_dsn)
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", _TEST_DB)
    if not exists:
        await conn.execute(f'CREATE DATABASE "{_TEST_DB}"')
    await conn.close()

    eng = create_async_engine(_TEST_URL, poolclass=NullPool)
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
        await c.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    sm = async_sessionmaker(engine, expire_on_commit=False)
    async with sm() as s:
        yield s


@pytest_asyncio.fixture(autouse=True)
async def _fresh_redis():
    """Rebind module-level async Redis clients to the current test's event loop.

    pytest-asyncio uses a fresh loop per test; a client cached on a previous
    (now-closed) loop raises 'Event loop is closed'. Recreating per test avoids it.
    """
    import redis.asyncio as aioredis

    import core.token_store as ts

    url = settings.redis_url
    ts._redis = aioredis.from_url(url, decode_responses=True)
    core.ratelimit._redis = aioredis.from_url(url, decode_responses=True)
    yield
    await ts._redis.aclose()
    await core.ratelimit._redis.aclose()


@pytest.fixture(autouse=True)
def _stub_externals(monkeypatch):
    core.ratelimit.settings.rate_limit_enabled = False
    monkeypatch.setattr("core.storage.upload_bytes", lambda *a, **k: None)
    monkeypatch.setattr("core.storage.delete_object", lambda *a, **k: None)
    monkeypatch.setattr(
        "core.storage.generate_presigned_url", lambda key, **k: f"http://minio/{key}"
    )
    monkeypatch.setattr("workers.tasks.ingestion.ingest_document.delay", lambda *a, **k: None)
    monkeypatch.setattr("workers.tasks.analysis.analyze_case.delay", lambda *a, **k: None)
    monkeypatch.setattr("workers.tasks.notifications.notify.delay", lambda *a, **k: None)


@pytest_asyncio.fixture
async def client(engine):
    sm = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db():
        async with sm() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    main.app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    main.app.dependency_overrides.clear()


# ── helpers ──────────────────────────────────────────────

_counter = {"n": 0}


def unique(prefix: str) -> str:
    _counter["n"] += 1
    return f"{prefix}{_counter['n']}"


async def make_tenant(client: AsyncClient, role_email: str | None = None):
    """Create a tenant + admin, return (admin_token, email, slug)."""
    slug = unique("t-")
    email = role_email or f"admin-{slug}@acme.com"
    await client.post(
        "/api/v1/tenants",
        json={"name": f"Org {slug}", "slug": slug, "admin_email": email, "admin_password": "password123"},
    )
    token = await login(client, email, "password123")
    return token, email, slug


async def login(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
