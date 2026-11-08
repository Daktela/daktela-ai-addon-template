import pytest
from cw_addons.utils.test_helpers import DiscussionBuilder
from fastapi.testclient import TestClient

from server.app import create_app
from server.di import Container
from unit_tests.conftest import TENANT_HEADERS


@pytest.mark.parametrize("profile", ["basic", "full"])
def test_example_order_skill_is_available_for_agent_selection(profile: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADDON_PROFILE", profile)
    client = TestClient(create_app(Container()))

    response = client.get("/skills", headers=TENANT_HEADERS)

    assert response.status_code == 200
    assert response.json()["skills"] == [
        {
            "key": "order_status",
            "name": "Order status",
            "load_when": "The customer asks about an order or its delivery.",
            "instructions": "Ask for the order number if it is missing. Use order_lookup and explain its returned status without inventing delivery dates.",
            "tools": ["order_lookup"],
        }
    ]


def test_skills_endpoint_requires_authentication() -> None:
    client = TestClient(create_app(Container()))
    headers = {key: value for key, value in TENANT_HEADERS.items() if key != "X-Api-Key"}

    response = client.get("/skills", headers=headers)

    assert response.status_code == 403


def test_manifest_advertises_skills_and_their_integration() -> None:
    client = TestClient(create_app(Container()))

    manifest = client.get("/manifest", headers=TENANT_HEADERS).json()

    assert manifest["has_skills"] is True
    assert {integration["name"] for integration in manifest["integrations"]} == {"order_lookup"}
    module = next(module for module in manifest["modules"] if module["name"] == "skill_catalog")
    assert [(attribute["name"], attribute["type"]) for attribute in module["attributes"]] == [("skills", "skills")]


@pytest.mark.parametrize(
    ("attributes", "expected"),
    [
        ({}, ""),
        ({"skills": []}, ""),
        ({"skills": None}, ""),
        ({"skills": [{"id": "42", "name": "Order status", "load_when": "Questions about orders"}]}, "Order status"),
    ],
)
def test_skill_selector_receives_only_opted_in_summaries(attributes: dict, expected: str) -> None:
    client = TestClient(create_app(Container()))

    response = client.post(
        "/module/v1/execute/skill_catalog",
        headers=TENANT_HEADERS,
        json={"attributes": attributes, "discussion": DiscussionBuilder().build().model_dump(mode="json")},
    )

    assert response.status_code == 200
    assert [(action["type"], action["text"]) for action in response.json()["actions"]] == [("message", expected)]
