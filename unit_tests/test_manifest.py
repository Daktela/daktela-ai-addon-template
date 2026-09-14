"""The manifest is the contract bot-platform reads. Guard its shape."""

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.di import Container

EXPECTED_MODULES = {
    "hello_world",
    "exchange_rate",
    "interaction_event",
    "tenant_settings",
    # Advanced examples - see docs/14-advanced.md.
    "streaming_echo",
    "local_tag",
}


@pytest.fixture(params=["full", "basic"])
def client(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Every manifest test runs in both profiles.

    The module surface is what both images exist to serve, so it has to be
    identical in either one. Only `has_setting` may differ - covered by
    `test_addon_profile.py`.
    """
    monkeypatch.setenv("ADDON_PROFILE", request.param)
    return TestClient(create_app(Container()))


def test_manifest_needs_an_api_key(client: TestClient) -> None:
    """A missing key is a 403, not a 401 - worth knowing when you connect the
    addon to bot-platform as a custom addon and see this in the logs."""
    assert client.get("/manifest").status_code == 403


def test_manifest_advertises_every_example_module(client: TestClient) -> None:
    manifest = client.get("/manifest", headers={"X-Api-Key": "default"}).json()

    assert manifest["code"] == "example"
    assert {module["name"] for module in manifest["modules"]} == EXPECTED_MODULES


def test_every_example_module_is_public(client: TestClient) -> None:
    """`public` is what puts a module in the flow builder's node palette."""
    manifest = client.get("/manifest", headers={"X-Api-Key": "default"}).json()

    assert all(module["public"] for module in manifest["modules"])


def test_manifest_advertises_the_function_integration(client: TestClient) -> None:
    """Only `function` integrations are useful today - see docs/08."""
    manifest = client.get("/manifest", headers={"X-Api-Key": "default"}).json()
    kinds = {integration["name"]: integration["type"] for integration in manifest["integrations"]}

    assert kinds == {"order_lookup": "function"}
