"""The addon's own HTTP API, called by its configuration page.

These routes are tagged `frontend`, which does two things:

* `GET /openapi-frontend.json` (registered in `server/app.py`) exposes only
  these routes, and that filtered schema is what Orval turns into the
  TypeScript client in `frontend/src/gen/` - run `make orval` after changing
  anything here.
* It keeps them separate from the routes `cw_addons` generates for
  the platform (`/manifest`, `/module/v1/*`, ...), which the frontend never
  calls directly.

Every route is scoped by `TenantDep`, which reads the `X-Customer`,
`X-Bot-Url`, `X-Instance-Id` and `X-Instance-Name` headers the platform
injects when it proxies a request from the configuration page, and validates
`X-Api-Key` along the way.
"""

from cw_addons.tenant_dep import TenantDep
from dependency_injector.wiring import inject
from fastapi import APIRouter, HTTPException

from server.di import SettingsStoreDep
from server.settings.models import ExampleCredentials, TenantKey

api_router = APIRouter(prefix="/api", tags=["frontend"])


def tenant_key(tenant: TenantDep) -> TenantKey:
    """Narrow the platform's `Tenant` down to the pair we store settings by.

    `Tenant` also carries `bot_url` and `instance_name`, which are useful for
    logging or for calling back into the platform but must not be part of the
    storage key - they can change without the tenant changing.
    """
    return TenantKey(customer=tenant.customer, instance_id=tenant.instance_id)


@api_router.get("/example_credentials", operation_id="getExampleCredentials")
@inject
async def get_example_credentials(tenant: TenantDep, store: SettingsStoreDep) -> ExampleCredentials:
    credentials = await store.get(tenant_key(tenant))

    if credentials is None:
        raise HTTPException(status_code=404, detail="This instance has no credentials stored yet")

    return credentials


@api_router.post("/example_credentials", operation_id="storeExampleCredentials")
@inject
async def store_example_credentials(
    credentials: ExampleCredentials,
    tenant: TenantDep,
    store: SettingsStoreDep,
) -> ExampleCredentials:
    """Create or replace this instance's credentials.

    Once a tenant has credentials, `GET /instance-configured` starts
    answering 200 instead of 409 - that is how the platform knows the addon
    is ready to be used. See `server/app.py`.
    """
    return await store.set(tenant_key(tenant), credentials)


@api_router.delete("/example_credentials", operation_id="deleteExampleCredentials")
@inject
async def delete_example_credentials(tenant: TenantDep, store: SettingsStoreDep) -> None:
    """Remove this instance's credentials. Idempotent: deleting nothing is fine."""
    await store.delete(tenant_key(tenant))
