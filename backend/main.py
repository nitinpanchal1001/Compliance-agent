from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1 import audit, auth, cases, documents, notifications, policies, tenants, users
from core.config import get_settings

log = structlog.get_logger()
settings = get_settings()

# Cap request bodies a little above the upload limit (headroom for multipart).
MAX_REQUEST_BYTES = (settings.max_upload_mb + 5) * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", env=settings.app_env)
    yield
    log.info("shutdown")


app = FastAPI(
    title="Compliance Intelligence Agent",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)


@app.middleware("http")
async def harden(request: Request, call_next):
    # Reject oversized bodies up front.
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > MAX_REQUEST_BYTES:
        return JSONResponse(
            {"detail": "Request body too large"},
            status_code=413,
        )
    response = await call_next(request)
    # Security headers on every response.
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(tenants.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(policies.router, prefix=API_PREFIX)
app.include_router(cases.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)


@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok"}


@app.get("/ready", tags=["ops"])
async def ready():
    checks: dict[str, str] = {}
    all_ok = True

    # Postgres
    try:
        import asyncpg
        conn = await asyncpg.connect(settings.database_url.replace("+asyncpg", ""))
        await conn.fetchval("SELECT 1")
        await conn.close()
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"
        all_ok = False

    # Redis
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        all_ok = False

    # Qdrant
    try:
        from qdrant_client import AsyncQdrantClient
        qc = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        await qc.get_collections()
        await qc.close()
        checks["qdrant"] = "ok"
    except Exception as e:
        checks["qdrant"] = f"error: {e}"
        all_ok = False

    status_code = 200 if all_ok else 503
    from fastapi.responses import JSONResponse

    return JSONResponse(
        {"status": "ready" if all_ok else "degraded", "checks": checks},
        status_code=status_code,
    )
