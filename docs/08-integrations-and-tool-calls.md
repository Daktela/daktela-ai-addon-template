# 8. Integrations and tool calls

A **module** is a node a human wires into a flow. An **integration** is a function the AI agent
decides to call on its own, mid-conversation, because it judged the tool relevant.

Worked example: `server/integrations/catalog/order_lookup.py`.

## Two kinds of integration

| `type` | Has `execute()` | What it is |
|---|---|---|
| `function` | yes | A tool the agent can call. Gets a `/integration/v1/execute/{name}` endpoint. |
| `widget` | no | A UI rendered in the chat window. **Do not use one yet** — see below. |

> **Widget integrations are not usable today.** The SDK lets you declare a `WidgetIntegration`, but
> the host half — the code that would render it in the chat window — is not built yet, and nothing in
> bot-platform reads the manifest's `has_widgets` flag. Worse, a `widget`-type integration still shows
> up in the builder's integration picker exactly like a function one, and wiring it would send
> the bot to `/integration/v1/execute/{name}`, which a `WidgetIntegration` does not implement. Declare
> one only when the platform supports it.

## A function integration

```python
class OrderLookupIntegration(Integration[OrderLookupAttributes]):
    name = "order_lookup"
    title = LangString(en="Order Lookup", cs="Vyhledání objednávky")
    description = "Look up the delivery status of a customer order by its ID."
    icon = "📦"
    version = "v1"

    arguments = [
        ToolArguments(
            name="order_id",
            description="The order identifier, in the format `order-12345`.",
            type=ToolAttributeTypeEnum.string,
            required=True,
        ),
    ]

    async def execute(self) -> IntegrationResponse:
        return IntegrationResponse(response={"order_id": ..., "status": "in_transit"})
```

Same conventions as modules: one class per file, in `server/integrations/catalog/`, discovered at
startup, published in `/manifest`.

## `description` is a prompt, not a label

This is the part people get wrong. `description` and each argument's `description` are read **by the
language model** when it decides whether to call your tool. They are prompt text.

Write them for a reader who has never seen your system:

```python
# Weak - the agent cannot tell when this applies
description = "Order API."

# Strong - states the purpose, the trigger, and the argument format
description = (
    "Look up the delivery status of a customer order by its ID. "
    "Use when the customer asks where their order is, or whether it has shipped. "
    "Requires the order ID in the format `order-12345`; ask the customer for it if unknown."
)
```

Rules of thumb:

- Say **when** to use it, not only what it does.
- Give the exact format of every argument, with an example.
- Say what it does *not* cover, if a neighbouring tool exists.
- Keep the returned `response` small and unambiguous — it goes back into the model's context, and a
  200-field JSON blob costs tokens and invites misreading.

## Argument types

`ToolAttributeTypeEnum` offers `string`, `number`, `boolean`, `object`, `array`. Mark an argument
`required=True` only when the tool genuinely cannot run without it — a required argument the customer
never mentions forces the agent to invent one or interrogate them.

## Tool calls from a module

A module can also ask the agent to run a tool and come back with the result. `ModuleExecutor` has:

```python
executor.add_tool_call(id="call-1", name="order_lookup", arguments={"order_id": "order-12345"})
```

The result arrives on the *next* execution of the module, in `discussion.tools_outputs`:

```python
if self.discussion.has_tool_output("call-1"):
    raw = self.discussion.get_tool_output("call-1")     # JSON string
```

So the round trip is: execute → request the tool call → the platform runs it → execute again with the
output available. Write the module to handle both passes, and use the store to remember where it got
to:

```python
if not self.discussion.has_tool_output("call-1"):
    executor.add_tool_call(id="call-1", name="order_lookup", arguments={...})
    return executor.get_response()

result = json.loads(self.discussion.get_tool_output("call-1"))
executor.add_message(f"Your order is {result['status']}.")
executor.add_output_port("done")
return executor.get_response()
```

## Calling it directly

```bash
curl -X POST localhost:8000/integration/v1/execute/order_lookup \
  -H "X-Api-Key: default" -H "X-Customer: local" -H "X-Bot-Url: https://your-instance.bot.daktela.com" \
  -H "X-Instance-Id: 1" -H "X-Instance-Name: local" \
  -H "Content-Type: application/json" \
  -d '{"attributes": {"order_id": "order-12345"}, "discussion": {"messages": [], "sequence": 0}}'
```

```json
{ "response": { "order_id": "order-12345", "status": "in_transit", "estimated_delivery": "2026-09-19" }, "billing_info": [] }
```

## Module or integration?

| Question | Answer |
|---|---|
| Should a human decide when it runs, and wire what happens next? | **Module** |
| Should the agent decide, based on what the customer said? | **Integration** (`function`) |
| Does it need its own UI in the chat? | Not supported yet — see the note above |
| Both? | Ship both; they can share an executor class. |

---

**Next:** [9. Dynamic lists](09-dynamic-lists.md).
