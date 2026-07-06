"""Synchronous DB session for Celery workers.

FastAPI uses the async engine in db/base.py. Celery tasks run synchronously, so
they use a separate sync engine here (psycopg driver). Both point at the same
Postgres database and share the same SQLAlchemy models.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import db.models  # noqa: F401 — registers all model mappers for FK resolution
from core.config import get_settings

settings = get_settings()

# Reuse the same DB URL but swap the async driver for the sync psycopg driver.
# asyncpg spells the TLS query param `ssl=`; psycopg (libpq) spells it `sslmode=`.
_sync_url = (
    settings.database_url.replace("+asyncpg", "+psycopg")
    .replace("?ssl=", "?sslmode=")
    .replace("&ssl=", "&sslmode=")
)

engine = create_engine(_sync_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@contextmanager
def get_sync_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
