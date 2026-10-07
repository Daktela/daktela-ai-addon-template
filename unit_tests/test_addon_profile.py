"""The two profiles, and the one missing route that is load-bearing."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.app import create_app
from server.di import Container
from server.profile import AddonProfile, addon_profile
from unit_tests.conftest import TENANT_HEADERS


def _api_paths(app: FastAPI) -> set[str]:
    """The app's own view of what it serves. Read from the OpenAPI schema
    rather than `app.routes`, which mixes route objects and router wrappers."""
    return set(app.openapi()["paths"])


@pytest.fixture
def basic_app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    monkeypatch.setenv("ADDON_PROFILE", "basic")
    return create_app(Container())


# --- the switch itself -----------------------------------------------------


def test_defaults_to_full_when_unset() -> None:
    assert addon_profile() is AddonProfile.FULL


def test_reads_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADDON_PROFILE", "basic")

    assert addon_profile() is AddonProfile.BASIC


def test_tolerates_casing_and_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    """The value usually arrives from a compose file or a k8s manifest."""
    monkeypatch.setenv("ADDON_PROFILE", "  Basic ")

    assert addon_profile() is AddonProfile.BASIC


def test_an_unknown_profile_refuses_to_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """A typo must not silently become `full` - see server/profile.py."""
    monkeypatch.setenv("ADDON_PROFILE", "bacis")

    with pytest.raises(ValueError, match="bacis"):
        addon_profile()


# --- what `basic` leaves out -----------------------------------------------


def test_basic_does_not_register_instance_configured(basic_app: FastAPI) -> None:
    """The one that would otherwise block activation.

    The platform blocks activation when `/instance-configured` answers 409, and
    treats a 404 as "nothing to configure". A basic addon has no configuration
    page, so it could never clear a 409 - the route must not exist at all.
    """
    assert "/instance-configured" not in _api_paths(basic_app)
    assert TestClient(basic_app).get("/instance-configured", headers=TENANT_HEADERS).status_code == 404


def test_basic_does_not_register_the_configuration_page_api(basic_app: FastAPI) -> None:
    assert "/api/example_credentials" not in _api_paths(basic_app)


def test_basic_does_not_expose_the_orval_schema(basic_app: FastAPI) -> None:
    """A 404 is the point: an *empty* schema would make `make orval` generate
    an empty client without complaining."""
    assert TestClient(basic_app).get("/openapi-frontend.json").status_code == 404


def test_basic_does_not_mount_the_frontend_bundle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """`FRONTEND_DIST` is faked, otherwise this would pass for the wrong
    reason: in CI there is no build and neither profile mounts anything."""
    monkeypatch.setattr("server.app.FRONTEND_DIST", tmp_path)

    monkeypatch.setenv("ADDON_PROFILE", "basic")
    basic = create_app(Container())
    monkeypatch.setenv("ADDON_PROFILE", "full")
    full = create_app(Container())

    def mount_names(app: FastAPI) -> set[str]:
        return {name for route in app.routes if (name := getattr(route, "name", None))}

    assert "frontend" not in mount_names(basic)
    assert "frontend" in mount_names(full)


# --- what `basic` keeps ----------------------------------------------------


def test_basic_serves_every_module(basic_app: FastAPI) -> None:
    """Modules are the point of the basic image."""
    manifest = TestClient(basic_app).get("/manifest", headers={"X-Api-Key": "default"}).json()

    assert len(manifest["modules"]) == 7
    assert manifest["has_setting"] is False


def test_basic_still_answers_register_addon(basic_app: FastAPI) -> None:
    """The only way a basic addon receives configuration from the platform."""
    response = TestClient(basic_app).post(
        "/api/register_addon",
        headers=TENANT_HEADERS,
        json={"envConfig": {"anything": "goes"}, "envVariables": {}},
    )

    assert response.status_code == 200


def test_basic_still_has_a_settings_store(basic_app: FastAPI) -> None:
    """The store stays in both profiles - `tenant_settings` reads it."""
    response = TestClient(basic_app).get("/readiness")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "profile": "basic", "backend": "json"}


# --- the contrast ----------------------------------------------------------


def test_full_registers_everything_basic_drops() -> None:
    paths = _api_paths(create_app(Container()))

    assert {"/instance-configured", "/api/example_credentials", "/api/register_addon"} <= paths


# --- identity --------------------------------------------------------------


def test_identity_defaults_let_a_fresh_clone_start() -> None:
    """`code` keeps a default on purpose: `uv run uvicorn` has to work with
    nothing configured. See server/identity.py."""
    from server.identity import addon_identity

    identity = addon_identity()

    assert identity.code == "example"
    assert identity.version == "1.0.0"


def test_identity_is_overridable_per_deployment(monkeypatch: pytest.MonkeyPatch) -> None:
    """One image, several environments - without a rebuild."""
    from server.identity import addon_identity

    monkeypatch.setenv("ADDON_CODE", "acme-crm")
    monkeypatch.setenv("ADDON_NAME", "Acme CRM (staging)")
    monkeypatch.setenv("ADDON_VERSION", "2.4.0")

    identity = addon_identity()

    assert (identity.code, identity.name, identity.version) == ("acme-crm", "Acme CRM (staging)", "2.4.0")


def test_identity_ignores_the_other_addon_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """`ADDON_PROFILE`, `ADDON_URL` and `ADDON_SETTINGS_FILE` share the prefix
    but belong to other parts of the addon. Reading identity must not choke on
    them."""
    from server.identity import addon_identity

    monkeypatch.setenv("ADDON_PROFILE", "basic")
    monkeypatch.setenv("ADDON_URL", "https://addon.example.com")
    monkeypatch.setenv("ADDON_SETTINGS_FILE", "/data/settings.json")

    assert addon_identity().code == "example"


def test_the_manifest_reports_the_configured_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADDON_CODE", "acme-crm")
    monkeypatch.setenv("ADDON_NAME", "Acme CRM")
    client = TestClient(create_app(Container()))

    manifest = client.get("/manifest", headers={"X-Api-Key": "default"}).json()

    assert manifest["code"] == "acme-crm"
    assert manifest["name"] == "Acme CRM"


def test_both_icon_kinds_reach_the_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    """The platform prefers `base64_icon` and falls back to `fa_icon`, so an
    addon may declare both and the manifest has to carry both."""
    monkeypatch.setenv("ADDON_BASE64_ICON", "data:image/png;base64,iVBORw0KGgo=")
    client = TestClient(create_app(Container()))

    manifest = client.get("/manifest", headers={"X-Api-Key": "default"}).json()

    assert manifest["base64_icon"] == "data:image/png;base64,iVBORw0KGgo="
    assert manifest["fa_icon"] == "puzzle-piece"


def test_the_icon_defaults_to_font_awesome_only() -> None:
    client = TestClient(create_app(Container()))

    manifest = client.get("/manifest", headers={"X-Api-Key": "default"}).json()

    assert manifest["fa_icon"] == "puzzle-piece"
    assert manifest["base64_icon"] is None
