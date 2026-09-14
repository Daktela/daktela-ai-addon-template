"""Alembic environment.

Migrations are only relevant once you enable persistence
(`docs/11-persistence.md`). Until then this file is never imported.

The connection string comes from the same `db_*` environment variables the
application uses, so `alembic upgrade head` and the running addon can never
disagree about which database they mean.
"""

import asyncio
import sys
from logging.config import fileConfig

if sys.platform == "win32":
    # See the same guard in server/main.py - psycopg's async driver needs the
    # selector event loop on Windows.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from alembic import context
from cw_utils import DBConnectionSettings
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Importing the table module is what gives autogenerate something to compare
# against. Add an import here for every new SQLModel table you create.
from server.settings import sql_table

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = sql_table.metadata

# Fallback matching docker-db/docker-compose.yaml, so `alembic upgrade head`
# works against the bundled dev database without extra configuration.
DEV_DATABASE_URL = "postgresql+psycopg://addon_user:addon_password@localhost:5442/addon_db"

settings = DBConnectionSettings()
config.set_main_option(
    "sqlalchemy.url",
    settings.connection_string() if settings.is_valid() else DEV_DATABASE_URL,
)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
