"""How the container decides where settings live.

The last test is the regression guard for the whole "database optional"
design: `CWSessionPool` raises when no connection is configured, so if the
container ever stopped being lazy, running without a database would break.
"""

import pytest
from dependency_injector import providers

from server.di import Container, storage_backend
from server.settings.json_store import JsonSettingsStore
from server.settings.sql_store import SqlSettingsStore

DB_ENV = {
    "db_host": "localhost",
    "db_port": "5442",
    "db_name": "addon_db",
    "db_username": "addon_user",
    "db_password": "addon_password",
}


def test_defaults_to_json_when_nothing_is_configured() -> None:
    assert storage_backend() == "json"


def test_switches_to_postgres_when_db_env_is_present(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in DB_ENV.items():
        monkeypatch.setenv(key, value)

    assert storage_backend() == "postgres"


def test_settings_store_env_var_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in DB_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("SETTINGS_STORE", "json")

    assert storage_backend() == "json"


def test_container_builds_the_json_store_by_default() -> None:
    assert isinstance(Container().settings_store(), JsonSettingsStore)


def test_container_builds_the_sql_store_when_asked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SETTINGS_STORE", "postgres")
    container = Container()
    container.config.connection_string.from_value("sqlite+aiosqlite:///:memory:")

    assert isinstance(container.settings_store(), SqlSettingsStore)


def test_no_database_mode_never_constructs_a_session_pool() -> None:
    """Resolving the store in json mode must not touch the Postgres branch.

    `CWSessionPool.__init__` raises without a connection string, so a container
    that eagerly built it would crash here.
    """
    container = Container()
    exploding = providers.Callable(_explode)
    container.session_pool.override(exploding)

    assert isinstance(container.settings_store(), JsonSettingsStore)


def _explode() -> None:
    raise AssertionError("the Postgres branch must not be constructed in json mode")
