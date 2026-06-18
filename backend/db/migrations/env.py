import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from core.config import get_settings
from db.base import Base

# Import all models so Alembic can detect them for autogenerate
from db.models.audit_log import AuditLog  # noqa: F401
from db.models.case import Case  # noqa: F401
from db.models.document import Document  # noqa: F401
from db.models.human_review import HumanReview  # noqa: F401
from db.models.policy import Policy  # noqa: F401
from db.models.tenant import Tenant  # noqa: F401
from db.models.user import User  # noqa: F401
from db.models.violation import Violation  # noqa: F401

config = context.config
settings = get_settings()

# Override sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
