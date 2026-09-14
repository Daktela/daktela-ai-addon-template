"""Liveness must not depend on anything; readiness must."""

import pytest
from dependency_injector import providers
from fastapi.testclient import TestClient

from server.app import create_app
from server.di import Container


class BrokenStore:
    name = "postgres"

    async def get(self, tenant):
        return None

    async def set(self, tenant, credentials):
        return credentials

    async def delete(self, tenant) -> None:
        return None

    async def health(self) -> None:
        raise ConnectionError("database is down")


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Container()))


def test_liveness_is_always_ok(client: TestClient) -> None:
    response = client.get("/liveness")

    assert response.status_code == 200
    assert response.json() == {"status": "alive", "profile": "full", "backend": None}


def test_readiness_reports_the_active_backend(client: TestClient) -> None:
    response = client.get("/readiness")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "profile": "full", "backend": "json"}


def test_readiness_returns_503_when_storage_is_down() -> None:
    container = Container()
    container.settings_store.override(providers.Object(BrokenStore()))
    client = TestClient(create_app(container))

    response = client.get("/readiness")

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "profile": "full", "backend": "postgres"}


def test_liveness_still_works_when_storage_is_down() -> None:
    container = Container()
    container.settings_store.override(providers.Object(BrokenStore()))
    client = TestClient(create_app(container))

    assert client.get("/liveness").status_code == 200
