"""Shared test fixtures.

The two autouse fixtures matter most. Without them a developer's local `.env`
or an exported variable would silently change what the suite tests: `db_*`
would switch everything to Postgres, and `ADDON_PROFILE=basic` - which anyone
who has run the basic image locally will have set - would drop the
configuration page, so those tests would fail with 404s that look exactly like
a routing bug.
"""

import os
from collections.abc import AsyncIterator, Iterator

import pytest
from cw_database.session_factory import provider_session_factory
from cw_database.session_pool import CWSessionPool

from server.settings import sql_table
from server.settings.json_store import JsonSettingsStore
from server.settings.sql_store import SqlSettingsStore
from server.settings.store import SettingsStore

TENANT_HEADERS = {
    "X-Api-Key": "default",
    "X-Customer": "test-customer",
    "X-Bot-Url": "https://your-instance.bot.daktela.com",
    "X-Instance-Id": "1",
    "X-Instance-Name": "test-instance",
}


@pytest.fixture(autouse=True)
def _isolate_storage_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for key in list(os.environ):
        if key.lower().startswith("db_"):
            monkeypatch.delenv(key, raising=False)

    monkeypatch.delenv("SETTINGS_STORE", raising=False)
    monkeypatch.delenv("ADDON_SETTINGS_FILE", raising=False)
    yield


@pytest.fixture(autouse=True)
def _isolate_profile_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Same idea as `_isolate_storage_env`, for the profile and the identity."""
    for key in (
        "ADDON_PROFILE",
        "ADDON_CODE",
        "ADDON_NAME",
        "ADDON_DESCRIPTION",
        "ADDON_VERSION",
        "ADDON_AUTHOR",
        "ADDON_FA_ICON",
        "ADDON_BASE64_ICON",
        "ADDON_COLOR",
    ):
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture(params=["json", "postgres"])
async def store(request: pytest.FixtureRequest, tmp_path) -> AsyncIterator[SettingsStore]:
    """Every store test runs twice: once per implementation.

    The SQL store runs on in-memory SQLite. `CWSessionPool` uses a StaticPool
    for sqlite URLs, so every session sees the same database - which is what
    lets CI exercise the real SQL code path without a Postgres server.
    """
    if request.param == "json":
        yield JsonSettingsStore(path=tmp_path / "settings.json")
        return

    pool = CWSessionPool(default_connection_string="sqlite+aiosqlite:///:memory:")
    async with pool.engine.begin() as connection:
        # Created from the model metadata rather than by running Alembic, so
        # this stays dialect-neutral. Migrations are checked separately.
        await connection.run_sync(sql_table.metadata.create_all)

    yield SqlSettingsStore(provider_session_factory(pool))

    await pool.engine.dispose()
