import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.models.base import Base

# Import every model module so that the tables are registered on
# Base.metadata before autogenerate inspects it. Without this the metadata
# is empty and autogenerate silently produces an empty migration.
from app.models import (  # noqa: F401  (imported for metadata side effects)
    audit,
    case,
    evidence,
    label,
    report_link,
    transaction,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def render_item(type_: str, obj: object, autogen_context: object) -> str | bool:
    """Render column types so the generated migration can be imported.

    The models declare JSON payloads as a generic JSON type with a
    PostgreSQL ``jsonb`` variant. SQLAlchemy inlines that variant into the
    migration as ``postgresql.JSONB(astext_type=Text())``, but Alembic does
    not emit the matching ``Text`` import, so the file raises ``NameError``
    when it is loaded. ``Text`` is already the default for that argument, so
    it is dropped here. Returning ``False`` falls back to the default
    rendering for every other type.
    """
    if type_ == "type" and isinstance(obj, postgresql.JSONB):
        autogen_context.imports.add("from sqlalchemy.dialects import postgresql")  # type: ignore[attr-defined]
        return "postgresql.JSONB()"
    return False


def run_migrations_offline() -> None:
    settings = get_settings()
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    settings = get_settings()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
