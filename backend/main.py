from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import auth, cases, documents, policies, tenants, users
from core.config import get_settings

log = structlog.get_logger()
settings = get_settings()


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
)


API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(tenants.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(policies.router, prefix=API_PREFIX)
app.include_router(cases.router, prefix=API_PREFIX)


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
