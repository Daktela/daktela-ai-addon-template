"""The specification of `SettingsStore`.

Every test here runs against both shipped implementations. If you add a third
one (Redis, a file per tenant, your own API), make it pass this file and the
rest of the addon will work unchanged.
"""

from server.settings.models import ExampleCredentials, TenantKey
from server.settings.store import SettingsStore

TENANT = TenantKey(customer="acme", instance_id=1)
OTHER_TENANT = TenantKey(customer="acme", instance_id=2)

CREDENTIALS = ExampleCredentials(api_url="https://api.example.com", api_token="token-1", display_name="Acme")
UPDATED = ExampleCredentials(api_url="https://api2.example.com", api_token="token-2", display_name="Acme 2")


async def test_get_returns_none_when_nothing_stored(store: SettingsStore) -> None:
    assert await store.get(TENANT) is None


async def test_set_then_get_roundtrips(store: SettingsStore) -> None:
    await store.set(TENANT, CREDENTIALS)

    assert await store.get(TENANT) == CREDENTIALS


async def test_set_twice_updates_instead_of_duplicating(store: SettingsStore) -> None:
    await store.set(TENANT, CREDENTIALS)
    await store.set(TENANT, UPDATED)

    assert await store.get(TENANT) == UPDATED


async def test_tenants_are_isolated(store: SettingsStore) -> None:
    await store.set(TENANT, CREDENTIALS)

    assert await store.get(OTHER_TENANT) is None


async def test_delete_removes_the_entry(store: SettingsStore) -> None:
    await store.set(TENANT, CREDENTIALS)
    await store.delete(TENANT)

    assert await store.get(TENANT) is None


async def test_delete_is_idempotent(store: SettingsStore) -> None:
    await store.delete(TENANT)  # must not raise


async def test_health_passes_when_storage_is_reachable(store: SettingsStore) -> None:
    await store.health()  # must not raise


def test_store_reports_a_name(store: SettingsStore) -> None:
    """`/readiness` surfaces this, so every implementation must set it."""
    assert store.name in {"json", "postgres"}
