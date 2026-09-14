"""Streaming a reply token by token instead of in one lump.

Demonstrates : `execute_streamed()`, the SSE envelope contract, and how the
               streamed chunks relate to the final actions.
Documented in: docs/14-advanced.md
Change first : the `_pieces()` generator - replace it with your LLM client, or
               whatever else produces text incrementally.

**This is an advanced topic.** A module does not need streaming; without it
the bot simply waits for the whole answer. Streaming is worth it when the
answer takes long enough that a customer would otherwise stare at a typing
indicator - typically an LLM call.

Defining `execute_streamed` is the only thing you do to opt in: the SDK checks
for the method, sets `supports_streaming` in the manifest, and registers
`POST /module/v1/execute/streaming_echo/stream` alongside the normal endpoint.
There is no flag to set.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import override

from cw_addons.modules.executor import ModuleExecutor
from cw_addons.modules.models import (
    LangString,
    ModuleResponses,
    NumberAttribute,
    OutputContext,
    OutputPortStatic,
    TextAreaAttribute,
)
from cw_addons.modules.module import Module
from cw_addons.modules.streaming import ChunkEvent, FinalEvent, StreamEnvelope
from pydantic import BaseModel


class StreamingEchoAttributes(BaseModel):
    text: str
    delay_ms: float


class StreamingEchoModule(Module[StreamingEchoAttributes]):
    attributes: StreamingEchoAttributes

    name = "streaming_echo"
    version = "v1"
    public = True

    icon = "⚡"
    category = LangString(en="Examples", cs="Příklady")
    title = LangString(en="Streaming Echo", cs="Streamovaná odpověď")
    short_description = LangString(
        en="Sends a message word by word, as a stream.",
        cs="Pošle zprávu slovo po slovu, streamovaně.",
    )
    description = LangString(
        en=(
            "Streams its answer word by word so the customer sees it appear as it is produced, "
            "then returns the same text as a normal message action. Replace the generator with a "
            "call to an LLM to make it useful."
        ),
        cs=(
            "Streamuje odpověď slovo po slovu, takže ji zákazník vidí přibývat, a nakonec vrátí "
            "stejný text jako běžnou zprávu. Generátor nahraďte voláním LLM."
        ),
    )

    input_attributes = [
        TextAreaAttribute(
            name="text",
            title=LangString(en="Text", cs="Text"),
            description=LangString(
                en="What to stream back, word by word.",
                cs="Co se má streamovat zpět, slovo po slovu.",
            ),
            default_value="This answer arrives one word at a time.",
            required=True,
        ),
        NumberAttribute(
            name="delay_ms",
            title=LangString(en="Delay between words (ms)", cs="Prodleva mezi slovy (ms)"),
            description=LangString(
                en="Only here to make the streaming visible; a real module has no such delay.",
                cs="Jen aby byl streaming vidět; skutečný modul takovou prodlevu nemá.",
            ),
            default_value=80,
        ),
    ]

    output_contexts = [
        OutputContext(
            name="streamed_text",
            title=LangString(en="Streamed text", cs="Streamovaný text"),
            description=LangString(en="The full text that was sent.", cs="Celý odeslaný text."),
        ),
    ]

    output_ports = [
        OutputPortStatic(
            name="done",
            title=LangString(en="Done", cs="Hotovo"),
            description=LangString(en="Always taken.", cs="Vždy."),
        ),
    ]

    @override
    async def execute(self) -> ModuleResponses:
        """The non-streaming path, and it is **not** optional.

        A streaming module must still answer the plain
        `POST /module/v1/execute/{name}` endpoint: `execute` is abstract on the
        base class, the route is always registered, and the platform falls back
        to it whenever it is not streaming this particular call.

        Keep the two paths in agreement. Here they share `_build_response`.
        """
        return self._build_response(self.attributes.text)

    async def execute_streamed(self) -> AsyncIterator[StreamEnvelope]:
        """The streaming path: zero or more chunks, then exactly one final event.

        Two rules that are easy to get wrong:

        * Each `ChunkEvent.delta` is an *increment*, not the text so far. The
          client concatenates them.
        * `FinalEvent.module_response` is a complete, ordinary `ModuleResponses`
          - the same one `execute()` would have returned, full message text and
          all. The chunks and the final message are two representations of the
          same answer, not two halves of it, so a client renders the chunks as
          they arrive and then takes everything else (output port, contexts,
          store, debug) from the final event without appending its text again.
        """
        streamed: list[str] = []

        for piece in self._pieces():
            streamed.append(piece)
            yield ChunkEvent(delta=piece)

            if self.attributes.delay_ms:
                await asyncio.sleep(self.attributes.delay_ms / 1000)

        # `done=True` marks the end of one logical message. A module that sends
        # several messages in a run emits one of these between them.
        yield ChunkEvent(delta="", done=True)

        yield FinalEvent(module_response=self._build_response("".join(streamed)))

    def _pieces(self) -> list[str]:
        """Whatever produces your text incrementally. An LLM client goes here."""
        words = self.attributes.text.split()
        return [word if index == 0 else f" {word}" for index, word in enumerate(words)]

    def _build_response(self, text: str) -> ModuleResponses:
        executor = ModuleExecutor(
            discussion=self.discussion,
            attributes=self.attributes,
            tenant=self.tenant,
            module_name=self.name,
        )

        executor.add_message(text)
        executor.add_context("streamed_text", text)
        executor.add_output_port("done")

        return executor.get_response()
