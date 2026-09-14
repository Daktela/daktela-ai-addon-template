"""Dependency injection container.

This is where the addon decides *where its settings live*. Everything else in
the application depends only on the `SettingsStore` protocol, so switching
between "no database" and "Postgres" is a configuration change, not a code
change.
"""

import os
from pathlib import Path
from typing import Annotated

from cw_database.session_factory import SessionFactory, provider_session_factory
from cw_database.session_pool import CWSessionPool
from cw_utils import DBConnectionSettings
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide
from fastapi import Depends

from server.settings.json_store import JsonSettingsStore
from server.settings.sql_store import SqlSettingsStore
from server.settings.store import SettingsStore


def storage_backend() -> str:
    """Which `SettingsStore` implementation to use: `"json"` or `"postgres"`.

    The default is `"json"` - no database, no Docker, nothing to install.
    Setting the `db_*` environment variables (see `.env.example`) switches the
    addon to Postgres automatically; `SETTINGS_STORE` forces either one.

    This is a plain function rather than a config value so that it is
    evaluated every time the container resolves the store - which is what
    makes it easy to flip in tests.
    """
    explicit = os.getenv("SETTINGS_STORE")
    if explicit:
        return explicit

    return "postgres" if DBConnectionSettings().is_valid() else "json"


def settings_file_path() -> Path | None:
    """Optional path the JSON store mirrors its contents to."""
    raw = os.getenv("ADDON_SETTINGS_FILE")
    return Path(raw) if raw else None


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # ---------------------------------------------------------------------
    # Level 1: no database (the default)
    # ---------------------------------------------------------------------
    json_store = providers.Singleton(
        JsonSettingsStore,
        path=providers.Callable(settings_file_path),
    )

    # ---------------------------------------------------------------------
    # Level 2: Postgres. See docs/11-persistence.md.
    #
    # Nothing in this block is constructed unless `storage_backend()` returns
    # "postgres" - `providers.Selector` only builds the branch it selects.
    # That matters: `CWSessionPool.__init__` raises when no connection is
    # configured, so eagerly building it would break the no-database default.
    #
    # Not using persistence at all? Delete this block and the `postgres=`
    # line below, then drop the database dependencies from pyproject.toml.
    # ---------------------------------------------------------------------
    session_pool = providers.Singleton(
        CWSessionPool,
        default_connection_string=config.connection_string,
    )
    session_factory: providers.Factory[SessionFactory] = providers.Factory(
        provider_session_factory,
        pool=session_pool,
    )
    sql_store = providers.Singleton(
        SqlSettingsStore,
        session_factory=session_factory,
    )

    # ---------------------------------------------------------------------
    # The one seam the rest of the application depends on.
    # ---------------------------------------------------------------------
    settings_store: providers.Provider[SettingsStore] = providers.Selector(
        providers.Callable(storage_backend),
        json=json_store,
        postgres=sql_store,
    )


# Use this in FastAPI routes:      async def route(store: SettingsStoreDep)
SettingsStoreProvider = Provide[Container.settings_store]
SettingsStoreDep = Annotated[SettingsStore, Depends(SettingsStoreProvider)]
