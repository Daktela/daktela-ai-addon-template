"""Behaviour specific to the default store."""

from pathlib import Path

import pytest

from server.settings.json_store import JsonSettingsStore
from server.settings.models import ExampleCredentials, TenantKey

TENANT = TenantKey(customer="acme", instance_id=1)
CREDENTIALS = ExampleCredentials(api_url="https://api.example.com", api_token="token-1", display_name="Acme")
OTHER_CREDENTIALS = ExampleCredentials(api_url="https://other.example.com", api_token="token-2", display_name="Other")


async def test_without_a_path_nothing_is_written(tmp_path: Path) -> None:
    store = JsonSettingsStore(path=None)
    await store.set(TENANT, CREDENTIALS)

    assert list(tmp_path.iterdir()) == []


async def test_contents_survive_a_restart_when_a_path_is_given(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"

    await JsonSettingsStore(path=path).set(TENANT, CREDENTIALS)
    reopened = JsonSettingsStore(path=path)

    assert await reopened.get(TENANT) == CREDENTIALS


async def test_a_failed_write_leaves_memory_untouched(tmp_path: Path) -> None:
    """A read-only volume must not produce a store that disagrees with its file."""
    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path=path)
    await store.set(TENANT, CREDENTIALS)

    def explode(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("read-only volume")

    original = Path.write_text
    Path.write_text = explode  # type: ignore[method-assign]
    try:
        with pytest.raises(PermissionError):
            await store.set(TENANT, OTHER_CREDENTIALS)
    finally:
        Path.write_text = original  # type: ignore[method-assign]

    assert await store.get(TENANT) == CREDENTIALS
