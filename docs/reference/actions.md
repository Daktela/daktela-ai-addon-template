# Reference: what an addon returns

Three kinds of call, three response shapes:

| Call | Returns |
|---|---|
| `POST /module/v1/execute/{name}` | `ModuleResponses` — the big one, below |
| `POST /integration/v1/execute/{name}` | `IntegrationResponse(response)` |
| `POST /dynamic_list/v1/{name}` | `DynamicListResponse(items)` — a list of `DynamicItem(value, label)` |
| `POST /module/v1/execute/{name}/stream` | Server-Sent Events, ending in a `ModuleResponses` — see [chapter 14](../14-advanced.md) |

The rest of this page is the module response, which is where all the richness is. Build it with
`ModuleExecutor` (recommended) or construct the pieces directly from `cw_addons.modules.models`.

## `ModuleResponses`

```python
ModuleResponses(
    actions=[...],        # what the platform should do - the bulk of this page
    debug=[...],          # diagnostic events -> the interaction's Events panel
    sequence=n + 1,       # discussion.sequence + 1
    ai_generated=False,   # was this answer produced by a model?
)
```

`get_response()` fills in `actions`, `debug` and `sequence` for you; the other two you set yourself
when they apply.

| Field | What it is for |
|---|---|
| `actions` | Everything the platform should do as a result of this execution. |
| `debug` | Diagnostics, stored per conversation. See [chapter 6](../06-events-in-interactions.md). |
| `sequence` | Ordering. Always `discussion.sequence + 1`; `ModuleExecutor` does it for you. |
| `ai_generated` | `True` if a language model produced the answer. The platform uses it to label AI-generated content. Set it yourself — nothing infers it. |

There is also a `billing_infos` field. It is internal to first-party addons; leave it empty.

## `ModuleExecutor` helpers

```python
executor = ModuleExecutor(
    discussion=self.discussion,
    attributes=self.attributes,
    tenant=self.tenant,
    module_name=self.name,
)
```

| Method | Produces | Use it for |
|---|---|---|
| `add_message(message, buttons=None)` | `MessageAction` | Text the customer sees, optionally with buttons |
| `add_context(key, value)` | folded into one `ContextAction` | A value later nodes in this flow can read |
| `add_store(payload: dict)` | `StoreAction` | A value that lives for the whole conversation |
| `add_output_port(port)` | `OutputPortAction` | Which arrow the flow follows |
| `add_debug_info(message, debug_type)` | a `DebugInfo` entry | A diagnostic event in the interaction |
| `add_tool_call(id, name, arguments)` | `ToolsCallAction` | Ask the agent to run an integration |
| `add_goal(goal)` | `GoalModuleAction` | Mark a business goal as reached (analytics + API) |
| `add_sender_metadata(metadata)` | `SenderMetadataAction` | Attach metadata to the sender |
| `wait_for_input()` | `WaitForInputAction` | Pause the flow until the customer replies |
| `get_last_message()` | — | Shortcut for the last customer message |
| `get_response()` | `ModuleResponses` | Always the last line of `execute()` |

## Action types

| Class | Fields | Meaning |
|---|---|---|
| `MessageAction` | `text`, `buttons: list[MessageButton]` | Send a chat message |
| `ContextAction` | `contexts: list[ResultContext]` | Set context variables (`ResultContext(name, value)`) |
| `StoreAction` | `store: dict[str, StoreValue]` | Write to the conversation store |
| `OutputPortAction` | `name` | Take this output port |
| `ToolsCallAction` | `tool_calls: list[FunctionToolCall]` | Request tool calls |
| `GoalModuleAction` | `goal`, `send_to_analytics`, `send_to_api` | Record a goal |
| `UserCommandsAction` | `user_commands: list[str]` | Set the user commands in play |
| `WaitForInputAction` | `user_commands: list[str]` | Wait for the customer |
| `SenderMetadataAction` | `metadata: dict` | Attach sender metadata |

## `MessageButton`

```python
executor.add_message(
    "Pick one",
    buttons=[MessageButton(text="Yes", payload='{"answer": "yes"}'),
             MessageButton(text="No",  payload='{"answer": "no"}')],
)
```

On the next execution:

```python
if self.discussion.has_selected_button():
    button = self.discussion.get_selected_button()   # .text, .payload
```

## `DebugInfo`

```python
from cw_addons.modules.models import DebugInfoType

executor.add_debug_info("CRM returned 503", DebugInfoType.error)   # info | warning | error
```

`debug_type` becomes the event's severity. See [chapter 6](../06-events-in-interactions.md).

## Reading the discussion

| Call | Returns |
|---|---|
| `get_last_customer_message()` | The customer's most recent text |
| `get_last_bot_message()` | The bot's most recent text |
| `get_conversation(limit=50)` | Recent turns, each truncated to 2000 chars |
| `get_conversation_with_metadata(limit=50)` | The same plus `mid` and `timestamp` |
| `has_context(key)` / `get_context_value(key, type, default=None)` | Context variables |
| `get_context()` | A `Context` helper supporting dotted paths (`get("a.b.c")`) |
| `has_store(key)` / `get_store_value(key, type, default=None)` | Store values (raises `TypeError` on a type mismatch) |
| `has_tool_output(id)` / `get_tool_output(id)` | Tool-call results (a JSON string) |
| `has_selected_button()` / `get_selected_button()` | The button the customer clicked |
| `get_language()` | `$sys_lang` from context, defaulting to `cs` |
| `to_chatgpt_messages()` | The conversation as OpenAI-style messages |

Fields: `messages`, `context`, `store`, `tools_outputs`, `sequence`,
`discussion_id`, `user_token`, `language`, `bot_type`, `instance_id`, `instance_name`, `instance_url`.

## `Tenant`

`self.tenant` — which bot-platform instance is calling.

| Field | Meaning |
|---|---|
| `customer` | Environment identifier |
| `instance_id` | The instance |
| `instance_name` | Its display name |
| `bot_url` | Its base URL |

`(customer, instance_id)` is the tenant key this template stores everything by.

## Context vs store vs event vs message

| | Visible to the customer | Lifetime | Use for |
|---|---|---|---|
| `add_message` | yes | the conversation | Something to say |
| `add_context` | no | this flow run | Values for later nodes |
| `add_store` | no | the conversation | Values that must outlive the flow run |
| `add_debug_info` | no | forever, in `discussion_events` | Explaining what happened, later |

## Typed context values

A declared `OutputContext` has a `context_type`, which tells the builder what later nodes can do with
the value: `text` (the default), `number`, `boolean`, `object` or `array`. It is a declaration about
the variable, not a conversion — what you pass to `add_context` is what gets stored.

## One arrow per item: `OutputPortList`

`OutputPortStatic` is a fixed arrow you name at build time. `OutputPortList` instead produces **one
arrow per item of a list your module puts in a context variable**, which is how a node offers a branch
per product, per queue, per search result.

```python
OutputPortList(
    name="per_product",
    title=LangString(en="Per product", cs="Podle produktu"),
    description=LangString(en="One branch per matched product.", cs="Jedna větev na produkt."),
    list_name="products",   # the context key holding the list
    list_key="sku",         # the field in each item that labels the arrow
)
```

Your module fills `products` with `add_context`, and the designer wires each resulting arrow.
