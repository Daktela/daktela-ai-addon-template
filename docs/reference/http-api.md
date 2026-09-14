# Reference: the HTTP surface

Every route your addon exposes, and who calls it. The ones marked *generated* are created by the SDK
from your catalogs — you never write them.

All of them require `X-Api-Key`.

## Called by bot-platform

| Method | Path | Generated | Purpose |
|---|---|---|---|
| `GET` | `/manifest` | ✔ | Everything the platform knows about your addon. ETag-cached. |
| `GET` | `/module/v1/catalog` | ✔ | Just the modules. |
| `POST` | `/module/v1/execute/{module_name}` | ✔ | Run a module. |
| `POST` | `/module/v1/execute/{module_name}/stream` | ✔ | Server-Sent Events, for modules that implement `execute_streamed` — [chapter 14](../14-advanced.md). Absent for the rest. |
| `POST` | `/integration/v1/execute/{name}` | ✔ | Run a function integration. |
| `POST` | `/dynamic_list/v1/{name}` | ✔ | Query a dynamic list. |
| `POST` | `/api/register_addon` | ✔ | The addon was synced to an instance. Registered only if you pass `on_register_addon`. |
| `GET` | `/instance-configured` | ✔ | Is this instance set up? 200 / 409. Registered only if you pass `on_check_configured` — **the `basic` profile does not**, because a 409 blocks activation. |

## Called by your own UI

**All of these exist only in the `full` profile.** In `basic` they are not registered at all.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/example_credentials` | Read this instance's settings. 404 if unset. |
| `POST` | `/api/example_credentials` | Create or replace them. |
| `DELETE` | `/api/example_credentials` | Remove them. Idempotent. |
| `GET` | `/dist/assets/addonBundle.js` | The federated bundle (served when `frontend/dist` exists). |

## Operational

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/liveness` | Is the process alive? Never touches a dependency. Reports the profile. |
| `GET` | `/readiness` | Can it serve traffic? Asks the settings store. 200 / 503. Reports the profile and the store. |
| `GET` | `/` | Swagger UI. |
| `GET` | `/openapi.json` | Full schema. |
| `GET` | `/openapi-frontend.json` | Only `frontend`-tagged routes. What Orval reads. `full` profile only. |
| `GET` | `/_codegen/v1/...` | A shadow OpenAPI app the SDK mounts so the platform can generate one shared client. Not yours to call. |

## Request shapes

**Module execution**

```json
POST /module/v1/execute/hello_world
{
  "attributes": { "greeting": "Hello!" },
  "discussion": {
    "messages": [{ "type": "customer", "message": "hi" }],
    "context": {},
    "store": {},
    "tools_outputs": [],
    "sequence": 0
  }
}
```

```json
{
  "actions": [
    { "type": "message", "text": "Hello!", "buttons": [] },
    { "type": "context", "contexts": [{ "name": "greeting_sent", "value": "Hello!" }] },
    { "type": "output_port", "name": "done" }
  ],
  "debug": [],
  "billing_infos": [],
  "sequence": 1,
  "ai_generated": false
}
```

**Integration execution**

```json
POST /integration/v1/execute/order_lookup
{ "attributes": { "order_id": "order-12345" }, "discussion": { "messages": [], "sequence": 0 } }
```

```json
{ "response": { "order_id": "order-12345", "status": "in_transit" }, "billing_info": [] }
```

**Dynamic list**

```json
POST /dynamic_list/v1/example_list
{ "query": "sup", "limit": 50, "page": 1 }
```

```json
{ "items": [{ "value": "technical_support", "label": "Technical Support" }] }
```

**Addon registration**

```json
POST /api/register_addon
{ "envConfig": { "...": "..." }, "envVariables": { "...": "..." } }
```

```json
{ "success": true, "detail": {} }
```

## Required headers

| Header | Sent on | Required by |
|---|---|---|
| `X-Api-Key` | everything | `cw_addons.security.get_api_key` |
| `X-Customer` | everything | `TenantDep`, `CWInstanceContext` |
| `X-Bot-Url` | everything | `TenantDep` |
| `X-Instance-Id` | everything | `TenantDep`, `CWInstanceContext` |
| `X-Instance-Name` | everything | `TenantDep` |
| `X-Discussion-Id`, `X-Message-Id`, `X-Request-Id`, `X-User-Token` | every call, for correlation | read them yourself if you need them |

## Status codes

| Code | When |
|---|---|
| 200 | Fine |
| 403 | `X-Api-Key` missing or not in `API_KEYS` |
| 404 | The resource does not exist (e.g. settings not saved yet) |
| 409 | `GET /instance-configured`: the instance is not configured |
| 422 | Missing or malformed headers or body |
| 503 | `GET /readiness`: the settings store is unreachable |

## Routes bot-platform exposes about your addon

Useful when debugging from the platform side:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/addons/test-manifest` | Fetch a manifest without saving |
| `POST` | `/api/addons/custom` | Register a custom addon by URL |
| `POST` | `/api/addons/sync` | Force a re-sync |
| `GET` | `/api/instance-addons?instanceId=` | Addons and their activation state |
| `GET` | `/api/addon/:id/addon-assets/*` | Proxy to your `dist/assets/*` |
| `ALL` | `/api/addon/:id/proxy/*` | Proxy to your addon, with headers injected |
| `GET` | `/api/discussions/:id/events` | The interaction's events — including yours |
