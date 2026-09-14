"""The data this addon stores per the platform tenant.

Everything in this file is *example* data. When you adapt this template to a
real addon, `ExampleCredentials` is the first class you should change - it is
the single source of truth for the database table, the request/response bodies
and the TypeScript client generated for the configuration page.
"""

from pydantic import BaseModel, Field


class TenantKey(BaseModel, frozen=True):
    """Identifies one the platform tenant.

    Bot-platform sends `X-Customer` and `X-Instance-Id` on every request it
    makes to an addon. The same pair is what `cw_addons` hands to the
    lifecycle callbacks (see `server/app.py`), so we use it as *the* tenant
    identity everywhere in this template - one concept, no translation layers.

    A single addon deployment serves many tenants. Never store settings in a
    module-level variable; always scope them by a `TenantKey`.
    """

    customer: str
    instance_id: int

    @property
    def storage_key(self) -> str:
        """Stable string form, used as the dict key by `JsonSettingsStore`."""
        return f"{self.customer}#{self.instance_id}"


class ExampleCredentials(BaseModel):
    """Per-tenant configuration entered on the addon's settings page.

    Replace these three fields with whatever your addon actually needs. The
    field names flow all the way through to the generated frontend client, so
    renaming one here and re-running `make orval` updates the UI types too.
    """

    api_url: str = Field(..., min_length=3, max_length=200, description="Base URL of the system this addon talks to")
    api_token: str = Field(
        ..., min_length=3, max_length=200, description="Token used to authenticate against that system"
    )
    display_name: str = Field(..., min_length=1, max_length=100, description="Human-readable label shown in the UI")
