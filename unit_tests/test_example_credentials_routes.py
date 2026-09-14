"""The configuration page's API, exercised against both storage backends.

The `store` fixture is parametrized, so every test here runs twice - once with
the JSON store and once against SQLite. Same routes, same assertions.
"""

import pytest
from dependency_injector import providers
from fastapi.testclient import TestClient

from server.app import create_app
from server.di import Container
from server.settings.store import SettingsStore
from unit_tests.conftest import TENANT_HEADERS

PAYLOAD = {"api_url": "https://api.example.com", "api_token": "token-1", "display_name": "Acme"}


@pytest.fixture
def client(store: SettingsStore) -> TestClient:
    container = Container()
    container.settings_store.override(providers.Object(store))
    return TestClient(create_app(container))


def test_requires_an_api_key(client: TestClient) -> None:
    headers = {key: value for key, value in TENANT_HEADERS.items() if key != "X-Api-Key"}

    assert client.get("/api/example_credentials", headers=headers).status_code == 403


def test_requires_the_tenant_headers(client: TestClient) -> None:
    response = client.get("/api/example_credentials", headers={"X-Api-Key": "default"})

    assert response.status_code == 422


def test_get_returns_404_before_anything_is_saved(client: TestClient) -> None:
    assert client.get("/api/example_credentials", headers=TENANT_HEADERS).status_code == 404


def test_save_then_read_back(client: TestClient) -> None:
    assert client.post("/api/example_credentials", headers=TENANT_HEADERS, json=PAYLOAD).status_code == 200

    response = client.get("/api/example_credentials", headers=TENANT_HEADERS)

    assert response.status_code == 200
    assert response.json() == PAYLOAD


def test_rejects_an_incomplete_payload(client: TestClient) -> None:
    response = client.post("/api/example_credentials", headers=TENANT_HEADERS, json={"api_url": "https://x"})

    assert response.status_code == 422


def test_delete_is_idempotent(client: TestClient) -> None:
    assert client.delete("/api/example_credentials", headers=TENANT_HEADERS).status_code == 200
    assert client.delete("/api/example_credentials", headers=TENANT_HEADERS).status_code == 200


def test_instance_configured_reflects_the_stored_settings(client: TestClient) -> None:
    """This is what bot-platform calls when an operator activates the addon."""
    assert client.get("/instance-configured", headers=TENANT_HEADERS).status_code == 409

    client.post("/api/example_credentials", headers=TENANT_HEADERS, json=PAYLOAD)
    assert client.get("/instance-configured", headers=TENANT_HEADERS).status_code == 200

    client.delete("/api/example_credentials", headers=TENANT_HEADERS)
    assert client.get("/instance-configured", headers=TENANT_HEADERS).status_code == 409


def test_register_addon_acknowledges_the_sync(client: TestClient) -> None:
    response = client.post(
        "/api/register_addon",
        headers=TENANT_HEADERS,
        json={"envConfig": {"anything": "goes"}, "envVariables": {}},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
