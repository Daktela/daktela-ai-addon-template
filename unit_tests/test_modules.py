"""Testing modules without HTTP.

`DiscussionBuilder` (shipped in the SDK) builds the conversation state a
module sees, so you can call `execute()` directly. This is the fastest way to
iterate on module logic - no bot-platform, no browser, no database.
"""

import httpx
import pytest
from cw_addons.utils.test_helpers import DiscussionBuilder, dummy_tenant

from server.modules.catalog.exchange_rate import ExchangeRateAttributes, ExchangeRateModule
from server.modules.catalog.hello_world import HelloWorldAttributes, HelloWorldModule
from server.modules.catalog.interaction_event import InteractionEventAttributes, InteractionEventModule


def _actions_of(response, action_type: str) -> list:
    return [action for action in response.actions if action.type == action_type]


async def test_hello_world_sends_the_greeting() -> None:
    module = HelloWorldModule(
        attributes=HelloWorldAttributes(greeting="Ahoj"),
        discussion=DiscussionBuilder().add_user_message("hi").build(),
        tenant=dummy_tenant,
    )

    response = await module.execute()

    assert _actions_of(response, "message")[0].text == "Ahoj"
    assert _actions_of(response, "output_port")[0].name == "done"


async def test_interaction_event_writes_a_debug_entry() -> None:
    """`response.debug` is what becomes a row in bot-platform's
    `discussion_events` table - see docs/06-events-in-interactions.md."""
    module = InteractionEventModule(
        attributes=InteractionEventAttributes(event_message="order 48271 not found", severity="warning"),
        discussion=DiscussionBuilder().add_user_message("where is my order").build(),
        tenant=dummy_tenant,
    )

    response = await module.execute()

    assert len(response.debug) == 1
    assert response.debug[0].message == "order 48271 not found"
    assert response.debug[0].debug_type == "warning"


async def test_interaction_event_also_sets_context_and_store() -> None:
    module = InteractionEventModule(
        attributes=InteractionEventAttributes(event_message="hello", severity="info"),
        discussion=DiscussionBuilder().build(),
        tenant=dummy_tenant,
    )

    response = await module.execute()

    contexts = _actions_of(response, "context")[0].contexts
    assert {context.name for context in contexts} == {"last_event_message"}
    assert _actions_of(response, "store")[0].store == {"example_addon_last_run": 0}


async def test_exchange_rate_converts(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(self, url, params=None, **kwargs):
        return httpx.Response(200, json={"rates": {"CZK": 25.0}}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    module = ExchangeRateModule(
        attributes=ExchangeRateAttributes(amount=10, source_currency="EUR", target_currency="CZK", timeout_seconds=5),
        discussion=DiscussionBuilder().build(),
        tenant=dummy_tenant,
    )

    response = await module.execute()

    assert _actions_of(response, "output_port")[0].name == "success"
    assert "250.0 CZK" in _actions_of(response, "message")[0].text


async def test_exchange_rate_takes_the_timeout_port_when_the_api_is_slow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A timeout is its own port, so the designer can retry instead of apologising."""

    async def timing_out_get(self, url, params=None, **kwargs):
        raise httpx.ReadTimeout("too slow")

    monkeypatch.setattr(httpx.AsyncClient, "get", timing_out_get)

    module = ExchangeRateModule(
        attributes=ExchangeRateAttributes(amount=10, source_currency="EUR", target_currency="CZK", timeout_seconds=2),
        discussion=DiscussionBuilder().build(),
        tenant=dummy_tenant,
    )

    response = await module.execute()

    assert _actions_of(response, "output_port")[0].name == "timeout"
    assert response.debug[0].debug_type == "warning"
    assert "2" in response.debug[0].message


async def test_exchange_rate_passes_the_configured_timeout_to_the_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The attribute has to reach httpx, or it is decoration."""
    seen: dict[str, object] = {}

    original_init = httpx.AsyncClient.__init__

    def recording_init(self, *args, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        original_init(self, *args, **kwargs)

    async def fake_get(self, url, params=None, **kwargs):
        return httpx.Response(200, json={"rates": {"CZK": 25.0}}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "__init__", recording_init)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    module = ExchangeRateModule(
        attributes=ExchangeRateAttributes(amount=10, source_currency="EUR", target_currency="CZK", timeout_seconds=3),
        discussion=DiscussionBuilder().build(),
        tenant=dummy_tenant,
    )

    await module.execute()

    assert seen["timeout"] == 3


async def test_exchange_rate_takes_the_error_port_when_the_api_answers_badly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_get(self, url, params=None, **kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx.AsyncClient, "get", failing_get)

    module = ExchangeRateModule(
        attributes=ExchangeRateAttributes(amount=10, source_currency="EUR", target_currency="CZK", timeout_seconds=5),
        discussion=DiscussionBuilder().build(),
        tenant=dummy_tenant,
    )

    response = await module.execute()

    assert _actions_of(response, "output_port")[0].name == "error"
    assert response.debug[0].debug_type == "error"
