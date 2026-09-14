# 7. Calling external APIs

Most addons exist to connect a bot to something else — a CRM, an ERP, an inventory system. This is the
part where a customer is waiting on the other end, so the failure behaviour matters as much as the
happy path.

Worked example: `server/modules/catalog/exchange_rate.py` and
`server/modules/executors/exchange_rate_executor.py`.

## Splitting the module from the executor

Once a module does real work, keep the class declarative and move the logic into an executor:

```python
# server/modules/catalog/exchange_rate.py
async def execute(self) -> ModuleResponses:
    return await ExchangeRateExecutor(
        discussion=self.discussion,
        attributes=self.attributes,
        tenant=self.tenant,
        module_name=self.name,
    ).run()
```

Why it is worth the extra file:

- The module file stays readable as *documentation of the node* — someone opening it sees the
  manifest, not a hundred lines of HTTP handling.
- `server/modules/executors/` is **not** scanned by the catalog loader, so executors are ordinary
  classes you can import, subclass and test without the framework involved.
- `ModuleExecutor` already gives you `add_message`, `add_context`, `add_output_port`,
  `add_debug_info` and `get_response()`.

Small modules do not need this. `hello_world.py` has no executor on purpose.

## Make the timeout an attribute, and honour it

The platform is blocked on your response while a real customer watches a typing indicator. A request
with no timeout will eventually hang one, and hanging is worse than failing: the customer gets
nothing and the flow designer gets no error path to react to.

So every outgoing call needs a timeout — and the person who knows how long this node may hold up an
interaction is the flow designer, not you. Make it an attribute:

```python
NumberAttribute(
    name="timeout_seconds",
    title=LangString(en="Timeout (seconds)", cs="Timeout (sekundy)"),
    description=LangString(
        en="How long to wait for the service before taking the timeout port.",
        cs="Jak dlouho čekat na službu, než se použije port timeout.",
    ),
    default_value=5,
    required=True,
)
```

and pass it straight through to the client:

```python
async def _fetch_rate(self, source: str, target: str, timeout_seconds: float) -> float:
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        response = await client.get(API_URL, params={"base": source, "symbols": target})
        response.raise_for_status()
        return float(response.json()["rates"][target])
```

Ship a sensible `default_value` — five seconds is reasonable for a synchronous lookup inside an
interaction — so a designer who does not care never has to think about it.

**The budget is for the whole node, not one call.** `httpx` enforces it for the request it is given;
if your module makes two calls, or retries, those all have to fit inside the same number. Nothing
enforces that for you.

`unit_tests/test_modules.py::test_exchange_rate_passes_the_configured_timeout_to_the_client` exists
because an attribute nobody passes on is just decoration.

## Give the timeout its own port

```python
output_ports = [
    OutputPortStatic(name="success", ...),
    OutputPortStatic(name="timeout", ...),
    OutputPortStatic(name="error",   ...),
]
```

A timeout is not the same failure as a bad response, and a designer usually wants to treat it
differently — retry once, or apologise and move on, instead of routing to the same dead end as a 500.
Splitting it out costs one port and one `except` clause:

```python
try:
    rate = await self._fetch_rate(source, target, attributes.timeout_seconds)
except httpx.TimeoutException:
    self.add_debug_info(
        message=f"Lookup timed out after {attributes.timeout_seconds}s",
        debug_type=DebugInfoType.warning,
    )
    self.add_message("The service is taking too long right now.")
    self.add_output_port("timeout")
    return self.get_response()
```

Note `httpx.TimeoutException` comes **before** the broader `httpx.HTTPError` clause — it is a
subclass, so the order matters.

## Fail into a port, not an exception

```python
try:
    rate = await self._fetch_rate(source, target, attributes.timeout_seconds)
except (httpx.HTTPError, KeyError, ValueError) as error:
    self.add_debug_info(
        message=f"Exchange-rate lookup {source}->{target} failed: {error}",
        debug_type=DebugInfoType.error,
    )
    self.add_message("Sorry, I could not reach the exchange-rate service right now.")
    self.add_output_port("error")
    return self.get_response()
```

Three things happen here, and all three matter:

1. **An event is recorded** with the actual reason, so whoever investigates later sees
   `ConnectTimeout` rather than silence ([chapter 6](06-events-in-interactions.md)).
2. **The customer is told something.** Not the exception — a sentence they can act on.
3. **The flow takes the `error` port**, so the designer can route to a human, retry, or apologise.

If you let the exception escape, the SDK catches it, records an error-level event and takes a port
named `other`. That keeps the bot alive, but the designer had no chance to handle it deliberately.
Treat it as the safety net it is.

## Declaring the failure path

```python
output_ports = [
    OutputPortStatic(name="success", title=LangString(en="Success", cs="Úspěch"), description=...),
    OutputPortStatic(name="timeout", title=LangString(en="Timeout", cs="Timeout"), description=...),
    OutputPortStatic(name="error",   title=LangString(en="Error",   cs="Chyba"),   description=...),
]
```

Describe what each port *means*, not what it is called. The designer wiring the flow has your
description and nothing else.

## Which HTTP client

`httpx.AsyncClient` is what the examples use: async, timeouts, and already a dependency.

If you want your outgoing calls to appear in the platform's distributed traces, `cw_utils` ships
`InstrumentedAsyncClient`, a drop-in replacement that propagates the trace context. Use it when you
have tracing set up; plain `httpx` is fine otherwise.

## Credentials

Never hard-code a token. Two options, in order of preference:

1. **Per tenant, from the settings page** — the operator enters them, you read them with the
   `SettingsStore` ([chapter 10](10-configuration-page.md)). `tenant_settings.py` shows the read:

   ```python
   credentials = await store.get(
       TenantKey(customer=self.tenant.customer, instance_id=self.tenant.instance_id)
   )
   ```

2. **Per deployment, from the environment** — fine when every tenant shares one upstream account.

Whichever you choose, do not put the value in a flow attribute: attributes are visible to everyone
who can open the flow, and they end up in exports.

## Rate limits and retries

- Retry only idempotent reads, at most once or twice, and only for timeouts and 5xx.
- Keep the total inside the designer's timeout budget: two retries of a 5-second call is a
  15-second wait, and nothing enforces that but you.
- Never retry a payment, an order or anything else that changes state.
- If the upstream rate-limits you, record an event and take the error port — do not sleep.

## Testing it

Patch the client; do not call the real API in tests. From `unit_tests/test_modules.py`:

```python
async def test_exchange_rate_takes_the_error_port_when_the_api_is_down(monkeypatch):
    async def failing_get(self, url, params=None, **kwargs):
        raise httpx.ConnectTimeout("boom")

    monkeypatch.setattr(httpx.AsyncClient, "get", failing_get)

    response = await module.execute()

    assert _actions_of(response, "output_port")[0].name == "error"
    assert response.debug[0].debug_type == "error"
```

Test the failure path first. It is the one that will run in production at three in the morning.

---

**Next:** [8. Integrations and tool calls](08-integrations-and-tool-calls.md).
