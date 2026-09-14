"""The streaming module, and the invariant that makes streaming safe.

The one worth protecting: the streamed chunks and the final response are two
representations of the *same* answer, not two halves of it. A client that
concatenated the chunks and then appended the final message text would show
everything twice.
"""

import pytest
from cw_addons.modules.streaming import ChunkEvent, FinalEvent
from cw_addons.utils.test_helpers import DiscussionBuilder, dummy_tenant
from fastapi.testclient import TestClient

from server.app import create_app
from server.di import Container
from server.modules.catalog.streaming_echo import StreamingEchoAttributes, StreamingEchoModule
from unit_tests.conftest import TENANT_HEADERS

TEXT = "one two three"


def _module(text: str = TEXT) -> StreamingEchoModule:
    return StreamingEchoModule(
        attributes=StreamingEchoAttributes(text=text, delay_ms=0),
        discussion=DiscussionBuilder().build(),
        tenant=dummy_tenant,
    )


async def _collect(module: StreamingEchoModule) -> list:
    return [event async for event in module.execute_streamed()]


async def test_chunks_are_increments_not_the_text_so_far() -> None:
    events = await _collect(_module())
    chunks = [event for event in events if isinstance(event, ChunkEvent)]

    assert "".join(chunk.delta for chunk in chunks) == TEXT


async def test_the_last_chunk_closes_the_message() -> None:
    events = await _collect(_module())
    chunks = [event for event in events if isinstance(event, ChunkEvent)]

    assert chunks[-1].done is True
    assert all(chunk.done is False for chunk in chunks[:-1])


async def test_exactly_one_final_event_and_it_comes_last() -> None:
    events = await _collect(_module())

    assert isinstance(events[-1], FinalEvent)
    assert sum(isinstance(event, FinalEvent) for event in events) == 1


async def test_the_final_response_carries_the_whole_answer() -> None:
    """Not the remainder - the whole thing, exactly as `execute()` would."""
    events = await _collect(_module())
    final = events[-1]
    assert isinstance(final, FinalEvent)

    messages = [action for action in final.module_response.actions if action.type == "message"]
    ports = [action for action in final.module_response.actions if action.type == "output_port"]

    assert messages[0].text == TEXT
    assert ports[0].name == "done"


async def test_the_streaming_and_plain_paths_agree() -> None:
    """Two code paths, one answer. This is the thing that drifts."""
    plain = await _module().execute()
    events = await _collect(_module())
    final = events[-1]
    assert isinstance(final, FinalEvent)

    assert final.module_response.actions == plain.actions


def test_the_module_advertises_streaming() -> None:
    """`supports_streaming` is computed from the presence of `execute_streamed`,
    not declared - so this is what catches a rename."""
    assert StreamingEchoModule.to_manifest().supports_streaming is True


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Container()))


def test_the_sse_endpoint_frames_every_event(client: TestClient) -> None:
    response = client.post(
        "/module/v1/execute/streaming_echo/stream",
        headers={**TENANT_HEADERS, "Accept": "text/event-stream"},
        json={
            "attributes": {"text": TEXT, "delay_ms": 0},
            "discussion": {"messages": [], "sequence": 0},
        },
    )

    frames = [line for line in response.text.splitlines() if line.startswith("data:")]

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert len(frames) == 5  # three words, the done marker, the final event
    assert '"type":"final"' in frames[-1]


def test_a_module_without_execute_streamed_has_no_stream_route(client: TestClient) -> None:
    """Only streaming modules get the endpoint."""
    response = client.post(
        "/module/v1/execute/hello_world/stream",
        headers={**TENANT_HEADERS, "Accept": "text/event-stream"},
        json={"attributes": {"greeting": "hi"}, "discussion": {"messages": [], "sequence": 0}},
    )

    assert response.status_code == 404


# --- the other advanced example: a module the platform runs itself ---------


def test_the_local_module_declares_itself_local() -> None:
    from server.modules.catalog.local_tag import LocalTagModule

    manifest = LocalTagModule.to_manifest()

    assert manifest.execution == "local"
    assert [action.type for action in manifest.local_actions] == ["context", "sender_metadata"]


async def test_the_local_module_fallback_renders_its_templates() -> None:
    """The platform normally interprets `local_actions` itself, but the plain
    execute route still exists for hosts that predate the flag - and the SDK's
    default implementation renders the same result."""
    from server.modules.catalog.local_tag import LocalTagAttributes, LocalTagModule

    module = LocalTagModule(
        attributes=LocalTagAttributes(tag="vip", source="flow"),
        discussion=DiscussionBuilder().build(),
        tenant=dummy_tenant,
    )

    response = await module.execute()
    context_action = next(action for action in response.actions if action.type == "context")
    contexts = context_action.contexts

    assert contexts[0].name == "conversation_tag"
    assert contexts[0].value == "vip"
