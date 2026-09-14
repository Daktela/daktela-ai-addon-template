"""The single seam between this addon and wherever its settings live.

Two implementations ship with the template:

* `JsonSettingsStore` - the default. Needs nothing: no Docker, no database.
* `SqlSettingsStore`   - Postgres via SQLModel. See `docs/11-persistence.md`.

The rest of the application only ever depends on this Protocol, which is what
makes the database optional. `server/di.py` picks an implementation at runtime.
"""

from typing import Protocol

from server.settings.models import ExampleCredentials, TenantKey


class SettingsStore(Protocol):
    """Per-tenant settings storage.

    Design notes, so the simplifications below do not read as oversights:

    * `get` returns `None` instead of raising. A missing row is a normal
      outcome, not an error - the route turns it into a 404 in one line.
    * `delete` is idempotent. Deleting settings that are not there succeeds.
    * `health` lives here, which makes this store the *only* piece of
      infrastructure the app depends on. That is what lets `/readiness` be
      three lines long (see `server/health.py`).
    * It is deliberately not generic over the payload type. `ExampleCredentials`
      is concrete so that adapting this template means editing one class.
    """

    name: str
    """`"json"` or `"postgres"`. Reported by `/readiness` so you can see which
    backend is live without reading the configuration."""

    async def get(self, tenant: TenantKey) -> ExampleCredentials | None:
        """Return the tenant's settings, or `None` if it has none yet."""
        ...

    async def set(self, tenant: TenantKey, credentials: ExampleCredentials) -> ExampleCredentials:
        """Create or replace the tenant's settings (an upsert)."""
        ...

    async def delete(self, tenant: TenantKey) -> None:
        """Remove the tenant's settings. Succeeds even if there were none."""
        ...

    async def health(self) -> None:
        """Raise if the backing storage is unreachable. Used by `/readiness`."""
        ...
