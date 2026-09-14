"""FastAPI application factory.

Read this file first. It is the whole wiring of the addon in one screen:

1. `addon_profile()` picks which surface this process exposes - `full`
   (backend plus configuration page) or `basic` (backend only). The two
   Docker images differ in that variable and nothing else. See
   `server/profile.py`.
2. `Settings(...)` describes the addon to the platform. Its identity - name,
   code, icon, version - comes from `server/identity.py`, which is the file
   you edit when you fork this template; the catalog paths stay here because
   they are about this repository's layout, not about the addon.
3. `ConfigurationService.configure_app` scans those catalogs and generates
   every route the platform calls: `/manifest`, `/module/v1/catalog`,
   `/module/v1/execute/{name}`, `/integration/v1/execute/{name}`,
   `/dynamic_list/v1/{name}`. You never write those by hand, and both
   profiles get all of them - the modules are the point of the addon.
4. `LifecycleService.register` adds the activation hooks:
   `POST /api/register_addon` in both profiles, `GET /instance-configured`
   only in `full`, for the reason spelled out at the call site.
5. The health probes, in both profiles.
6. Last, in one block: everything that exists only in the `full` profile.
"""

import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from cw_addons.models import Settings
from cw_addons.service.configuration_service import ConfigurationService
from cw_addons.service.lifecycle_service import (
    AddonRegisterRequest,
    AddonRegisterResponse,
    CWInstanceContext,
    LifecycleService,
)
from cw_addons.utils.openapi_helper import build_openapi_for_tag
from dependency_injector.wiring import inject
from fastapi import FastAPI
from loguru import logger
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from server.api.example_credentials import api_router
from server.di import Container, SettingsStoreDep, SettingsStoreProvider
from server.health import HealthResponse
from server.identity import addon_identity
from server.profile import AddonProfile, addon_profile
from server.settings.models import TenantKey
from server.settings.store import SettingsStore

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def create_app(container: Container) -> FastAPI:
    # ------------------------------------------------------------------
    # 1. Which addon are we today?
    # ------------------------------------------------------------------
    profile = addon_profile()
    is_full = profile is AddonProfile.FULL
    identity = addon_identity()

    # Worth a line in the log: it is how you tell which addon and which
    # profile a running container actually is, and it makes a forgotten
    # placeholder `code` visible the first time anyone reads the log.
    logger.info(
        "Serving addon '{}' ({}) v{}, profile {}",
        identity.code,
        identity.name,
        identity.version,
        profile.value,
    )

    app = FastAPI(
        title=identity.name,
        description=identity.description,
        version="1.0.0",
        docs_url="/",
        # Set ROOT_PATH when the addon is served under a path prefix by a
        # reverse proxy, so the generated OpenAPI URLs stay correct.
        root_path=os.environ.get("ROOT_PATH", ""),
    )

    # ------------------------------------------------------------------
    # 2 + 3. Who this addon is, and where its catalogs are.
    #
    # Edit the identity in `server/identity.py`, or override any of it with
    # an ADDON_-prefixed environment variable.
    # ------------------------------------------------------------------
    settings = Settings(
        code=identity.code,
        name=identity.name,
        description=identity.description,
        version=identity.version,
        author=identity.author,
        # Both are passed; the platform prefers base64_icon when it is set
        # and falls back to the Font Awesome name otherwise.
        fa_icon=identity.fa_icon,
        base64_icon=identity.base64_icon,
        color=identity.color,
        # Where the catalogs live, relative to this file. Unlike the identity
        # above, these describe the repository and never vary per deployment.
        root_path=__file__,
        module_catalog_path="modules/catalog",
        integration_catalog_path="integrations/catalog",
        dynamic_list_catalog_path="dynamic_lists/catalog",
        # Only the full profile ships a configuration page. `has_setting`
        # is what puts the "Configure" button on the addon's card.
        has_setting=is_full,
    )

    ConfigurationService.configure_app(app=app, settings=settings)

    # ------------------------------------------------------------------
    # 4. Activation lifecycle.
    # ------------------------------------------------------------------
    LifecycleService.register(
        app,
        on_register_addon=_register_addon,
        # Omitting the callback leaves `GET /instance-configured` unregistered,
        # and that is deliberate, not a shortcut. The route answers 409 until a
        # tenant has saved settings, and the platform refuses to activate an
        # addon whose /instance-configured says 409. A basic addon has no
        # configuration page, so nothing could ever clear that 409 and the
        # addon could never be activated. An absent route 404s instead, which
        # the platform reads as "nothing to configure here".
        on_check_configured=_check_configured if is_full else None,
    )

    # ------------------------------------------------------------------
    # 5. Health probes - both profiles.
    # ------------------------------------------------------------------
    app.add_api_route("/liveness", _liveness_route(profile), methods=["GET"], tags=["infra"])
    app.add_api_route("/readiness", _readiness_route(profile), methods=["GET"], tags=["infra"])

    # ------------------------------------------------------------------
    # 6. The `full` profile only: this addon's configuration page.
    #
    # Everything in this block - and nothing outside it - is what the `basic`
    # image leaves out.
    # ------------------------------------------------------------------
    if is_full:
        # The API the configuration page calls.
        app.include_router(api_router)

        # The schema Orval generates the frontend client from.
        app.add_api_route(
            "/openapi-frontend.json",
            lambda: _openapi_frontend(app),
            methods=["GET"],
            include_in_schema=False,
        )

        # The built configuration page bundle. Guarded, so the backend starts
        # before you have ever run `pnpm build`.
        if FRONTEND_DIST.is_dir():
            app.mount("/dist", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
        else:
            logger.info("frontend/dist not found - serving API only. Run `make frontend-build` to add the UI.")

    ConfigurationService.wire_container(container=container)

    return app


# ----------------------------------------------------------------------
# Lifecycle callbacks
# ----------------------------------------------------------------------
@inject
async def _check_configured(
    context: CWInstanceContext,
    store: SettingsStore = SettingsStoreProvider,
) -> bool:
    """Answers `GET /instance-configured`: has this tenant been set up?

    `True` becomes 200, `False` becomes 409. Bot-platform calls this when an
    operator activates the addon, and shows the 409 as "not configured yet".
    """
    return await store.get(TenantKey(customer=context.customer, instance_id=context.instance_id)) is not None


@inject
async def _register_addon(
    request: AddonRegisterRequest,
    context: CWInstanceContext,
    store: SettingsStore = SettingsStoreProvider,
) -> AddonRegisterResponse:
    """Answers `POST /api/register_addon`: the platform synced this addon.

    A real addon typically seeds its settings from `request.env_config` here,
    for example:

        await store.set(
            TenantKey(customer=context.customer, instance_id=context.instance_id),
            ExampleCredentials(**request.env_config),
        )

    This template only logs, so that registering never silently overwrites
    credentials an operator typed in by hand.
    """
    _ = store
    logger.info(
        "Addon registered for customer={} instance_id={} config_keys={}",
        context.customer,
        context.instance_id,
        sorted(request.env_config),
    )
    return AddonRegisterResponse(success=True)


# ----------------------------------------------------------------------
# Health probes - see server/health.py for why they differ
# ----------------------------------------------------------------------
def _liveness_route(profile: AddonProfile) -> Callable[[], Awaitable[HealthResponse]]:
    async def _liveness() -> HealthResponse:
        return HealthResponse(status="alive", profile=profile.value)

    return _liveness


def _readiness_route(profile: AddonProfile) -> Callable[..., Awaitable[JSONResponse]]:
    """Bind the profile once, at boot, so a probe can never disagree with the
    routing table it was built alongside."""

    @inject
    async def _readiness(store: SettingsStoreDep) -> JSONResponse:
        try:
            await store.health()
        except Exception:
            logger.exception("Readiness check failed")
            return JSONResponse(
                status_code=503,
                content=HealthResponse(status="unhealthy", profile=profile.value, backend=store.name).model_dump(),
            )

        return JSONResponse(
            status_code=200,
            content=HealthResponse(status="healthy", profile=profile.value, backend=store.name).model_dump(),
        )

    return _readiness


def _openapi_frontend(app: FastAPI) -> dict[str, Any]:
    """The schema Orval generates the frontend client from - `frontend`-tagged routes only."""
    return build_openapi_for_tag("frontend", app)
