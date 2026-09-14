# 12. Testing

The fastest feedback loop for addon development is a unit test, not a browser and not a conversation.

```bash
make test        # backend + frontend
uv run pytest    # backend only
uv run pytest unit_tests/test_modules.py -k exchange    # one thing
```

## Testing a module

A module is a class you can construct. The SDK ships `DiscussionBuilder` to fake the conversation:

```python
from cw_addons.utils.test_helpers import DiscussionBuilder, dummy_tenant

async def test_hello_world_sends_the_greeting() -> None:
    module = HelloWorldModule(
        attributes=HelloWorldAttributes(greeting="Ahoj"),
        discussion=DiscussionBuilder().add_user_message("hi").build(),
        tenant=dummy_tenant,
    )

    response = await module.execute()

    assert response.actions[0].text == "Ahoj"
```

No HTTP, no platform, no database. `unit_tests/test_modules.py` has the full set.

### `DiscussionBuilder`

```python
DiscussionBuilder()
    .add_user_message("where is my order")
    .add_bot_message("Let me check")
    .set_context(key="order_id", value="order-12345")
    .set_store({"cart": {"items": 3}})
    .set_language("cs")
    .set_instance(instance_name="acme", instance_id=7)
    .set_sequence(4)
    .set_tools_outputs([...])
    .build()
```

Build exactly the state the branch under test needs, and nothing else — a test that sets five fields
to exercise one of them is a test nobody will update later.

### Asserting on actions

Actions are a heterogeneous list, so filter by type:

```python
def _actions_of(response, action_type: str) -> list:
    return [action for action in response.actions if action.type == action_type]

assert _actions_of(response, "output_port")[0].name == "success"
assert _actions_of(response, "message")[0].text == "10.0 EUR is 250.0 CZK."
```

Worth asserting on, in rough order of value:

1. **Which output port** was taken — that is the flow's behaviour.
2. **Debug entries** — `response.debug[0].debug_type == "error"` on failure paths.
3. **Context and store** values later nodes depend on.
4. Message text, when the wording actually matters.

## Testing external calls

Patch the client. Never call the real API:

```python
async def test_takes_the_error_port_when_the_api_is_down(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_get(self, url, params=None, **kwargs):
        raise httpx.ConnectTimeout("boom")

    monkeypatch.setattr(httpx.AsyncClient, "get", failing_get)

    response = await module.execute()

    assert _actions_of(response, "output_port")[0].name == "error"
    assert response.debug[0].debug_type == "error"
```

Write the failure test first. It is the path that runs unattended at three in the morning, and the one
nobody exercises by hand.

## Testing routes

`TestClient` plus a container override gives you the real app with a fake store:

```python
@pytest.fixture
def client(store: SettingsStore) -> TestClient:
    container = Container()
    container.settings_store.override(providers.Object(store))
    return TestClient(create_app(container))
```

Because the `store` fixture is parametrized, every route test runs against both storage backends for
free. `unit_tests/test_example_credentials_routes.py` covers 403 without an API key, 422 without
tenant headers, the 404/200 lifecycle and `/instance-configured` flipping between 409 and 200.

Remember the headers:

```python
TENANT_HEADERS = {
    "X-Api-Key": "default",
    "X-Customer": "test-customer",
    "X-Bot-Url": "https://your-instance.bot.daktela.com",
    "X-Instance-Id": "1",
    "X-Instance-Name": "test-instance",
}
```

## Testing the manifest

The manifest is the contract with the platform, so guard its shape:

```python
def test_every_example_module_is_public(client: TestClient) -> None:
    manifest = client.get("/manifest", headers={"X-Api-Key": "default"}).json()
    assert all(module["public"] for module in manifest["modules"])
```

`unit_tests/test_manifest.py` catches a whole class of "why is my module not in the builder" problems
before you go looking in the UI.

## Environment isolation

`unit_tests/conftest.py` strips `db_*`, `SETTINGS_STORE` and `ADDON_SETTINGS_FILE` from the
environment for every test:

```python
@pytest.fixture(autouse=True)
def _isolate_storage_env(monkeypatch: pytest.MonkeyPatch):
    for key in list(os.environ):
        if key.lower().startswith("db_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("SETTINGS_STORE", raising=False)
```

Without it, a developer with a local `.env` would silently run the whole suite against Postgres, and
the "works with no database" tests would stop testing that.

## Frontend tests

```bash
cd frontend && pnpm test
```

Vitest plus Testing Library. `tests/settingsPage.test.tsx` renders the settings page with `addonAxios`
mocked and checks the states that matter: the empty form on a 404, a prefilled form, a valid submit,
and a rejected invalid one.

Mock at the axios instance, not at `fetch` — that is the same seam the platform's proxy plugs into.

## Coverage

```bash
make coverage
```

Chase coverage of *branches you care about*, not a number. The branches worth having covered in an
addon: every output port, every failure path, both storage backends, and the manifest.

## What CI runs

`.github/workflows/ci.yml`: ruff, `ruff format --check`, pyright and pytest for the backend; eslint,
tsc, vitest and a production build for the frontend. No services — the SQL store runs on SQLite.

`make check` runs the same thing locally.

---

**Next:** [13. Deployment](13-deployment.md).
