"""A function integration: a tool the AI agent can call on its own.

Demonstrates : exposing addon functionality as an LLM tool call.
Documented in: docs/08-integrations-and-tool-calls.md
Change first : `arguments` and the `execute()` body.

Modules vs integrations, in one line: a **module** is a node the flow designer
drags onto the canvas and wires up; an **integration** is a function the AI
agent decides to call, described well enough that a language model can pick it.
"""

from typing import override

from cw_addons.integrations.integration import Integration, IntegrationResponse
from cw_addons.modules.models import LangString, ToolArguments, ToolAttributeTypeEnum
from pydantic import BaseModel


class OrderLookupAttributes(BaseModel):
    order_id: str


class OrderLookupIntegration(Integration[OrderLookupAttributes]):
    attributes: OrderLookupAttributes

    name = "order_lookup"
    version = "v1"

    icon = "📦"
    title = LangString(en="Order Lookup", cs="Vyhledání objednávky")
    description = "Look up the delivery status of a customer order by its ID."
    """Written for the language model, not for a human. Be explicit about when
    the tool should be used and what the arguments look like - this text is
    what the agent reasons over when deciding whether to call it."""

    arguments = [
        ToolArguments(
            name="order_id",
            description="The order identifier, in the format `order-12345`.",
            type=ToolAttributeTypeEnum.string,
            required=True,
        ),
    ]

    @override
    async def execute(self) -> IntegrationResponse:
        """Whatever you put in `response` is handed back to the agent as the
        tool result, so keep it small and unambiguous."""
        return IntegrationResponse(
            response={
                "order_id": self.attributes.order_id,
                "status": "in_transit",
                "estimated_delivery": "2026-09-19",
            }
        )
