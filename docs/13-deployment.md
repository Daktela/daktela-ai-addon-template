# 13. Deployment

An addon is an ordinary HTTP service. Anything that runs a container will host it.

This is where an addon belongs: on a server, at its own address, running whether or not anyone's
laptop is open. The tunnels in [chapter 3](03-connect-to-bot-platform.md) exist so you can try
things during development — they are not a deployment.

## Two images

| | `basic` | `full` |
|---|---|---|
| Build | `make docker-build-basic` | `make docker-build` |
| Dockerfile | `docker/Dockerfile.basic` | `docker/Dockerfile` |
| Contains | the backend | the backend plus the built configuration page |
| Node in the build | no | yes |
| `ADDON_PROFILE` | `basic` | `full` |

Pick `basic` unless an operator has something to configure. The reason is not size — the two images
are within a couple of megabytes of each other, because the Python environment dominates and the
frontend never reaches the runtime layer anyway. The reasons are a manifest that tells the truth
(`has_setting: false`, no `/instance-configured`) and a build with no Node in it.

```bash
make docker-build-basic
docker run -p 8000:8000 -e API_KEYS=<a real secret> example-addon-basic:local
```

`docker/Dockerfile` is three stages: Node builds the federated frontend bundle, a Python builder
compiles the dependencies, and the runtime image takes the finished virtualenv plus `dist/`.
`docker/Dockerfile.basic` is the same minus the Node stage. One container serves the API and the UI, which keeps the
manifest URL and the asset URL on the same origin — which is what bot-platform expects.

```bash
docker compose -f docker/compose.yaml up --build -d addon         # full,  :8000
docker compose -f docker/compose.yaml up --build -d addon-basic   # basic, :8001
curl localhost:8000/liveness   # {"status":"alive","profile":"full"}
```

`docker/compose.yaml` runs the same image with a volume for the JSON settings file, and has the
Postgres service commented out for when you want it.

Three details in the image that are easy to get wrong if you rewrite it:

- **`.dockerignore` matters.** Without it, `COPY frontend/ ./` drops your machine's `node_modules`
  (with its platform-specific binaries) over the ones installed in the container, and the frontend
  build fails confusingly.
- **The build stage needs a compiler.** `cw-database` depends on `psycopg2`, which is source-only, so
  the builder installs `build-essential` and `libpq-dev`. The runtime image gets only `libpq5` and the
  finished virtualenv.
- **`/data` is created and chowned in the image.** The container runs as a non-root user, and a named
  volume inherits the ownership of the directory it is mounted over. Skip that and
  `ADDON_SETTINGS_FILE` fails with `PermissionError` on the first save.

## Environment

| Variable | Required | Notes |
|---|---|---|
| `ADDON_PROFILE` | no | `full` (default) or `basic`. An unrecognised value refuses to start. |
| `API_KEYS` | **yes, in production** | Comma-separated. Unset means the SDK accepts the literal key `default` — fine locally, unacceptable in production. |
| `ADDON_URL` | if signed | Your public URL. Only matters for first-party addons that carry a manifest signature. |
| `ROOT_PATH` | if proxied under a path | Keeps the generated OpenAPI URLs correct. |
| `ADDON_SETTINGS_FILE` | no | Makes the default store survive a restart. Put it on a volume. |
| `db_host`, `db_port`, `db_name`, `db_username`, `db_password` | no | All five present switches to Postgres. |
| `SETTINGS_STORE` | no | `json` / `postgres`, overriding the detection. |

Full list with defaults: [reference/env-vars.md](reference/env-vars.md).

## Health probes

| Probe | Endpoint | Fails when |
|---|---|---|
| Liveness | `GET /liveness` | The process is wedged. Never on a database problem. |
| Readiness | `GET /readiness` | The settings store is unreachable (503). |

Do not point liveness at `/readiness`. A brief database outage would restart every healthy replica
and turn a small problem into a large one.

## Migrations

Only if you enabled persistence. Run them as a step before the new version starts serving:

```bash
uv run alembic upgrade head
```

In Kubernetes that is an init container or a Job that must complete before the rollout.

## Requirements checklist

Before pointing bot-platform at a deployed addon:

- [ ] **Running on a server**, not behind a development tunnel.
- [ ] **HTTPS**, with a certificate the platform trusts.
- [ ] `API_KEYS` set to a real secret, and the same value configured as the custom header in the admin
      UI.
- [ ] `GET /manifest` answers 200 with the right key, 403 without.
- [ ] `GET /dist/assets/addonBundle.js` answers 200 — full profile only.
- [ ] `GET /instance-configured` answers 200 or 404, never 409, or the addon cannot be activated.
- [ ] `GET /liveness` reports the profile you meant to deploy.
- [ ] `/liveness` and `/readiness` wired to the orchestrator.
- [ ] Migrations applied (if using Postgres).
- [ ] Logs going somewhere you can read them.

Then follow [chapter 3](03-connect-to-bot-platform.md), using your public URL instead of
`localhost:8000`.

## Versioning

Two rules save the most pain:

1. **Never rename a published module's `name`.** Bot-platform stores it inside saved flows; renaming
   orphans the node in every flow that used it. Ship a new module and deprecate the old one instead.
2. **Adding attributes is safe; removing or renaming them is not.** Give every new attribute a
   `default_value` so existing flows keep working.

The same goes for a dynamic list's `value`s: they are saved inside flows.

## Scaling

- The addon is stateless **if** you use the SQL store. With the JSON store each replica has its own
  copy of the settings, so run one replica or accept the divergence.
- Module executions are independent; scale horizontally.
- Your upstream API is usually the bottleneck, not the addon. Cache what is cacheable, and honour
  rate limits ([chapter 7](07-calling-external-apis.md)).

## Observability

The template ships without tracing or error reporting, to keep the reading surface small. Both are
straightforward to add:

**OpenTelemetry** — `cw_utils` reads `OTEL_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`,
`OTEL_SERVICE_NAME`. Instrument the app in `create_app`:

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()
```

and use `cw_utils.InstrumentedAsyncClient` for outgoing calls so traces span the boundary.

**Sentry** — `sentry-sdk[fastapi]`, initialised from `SENTRY_DSN` / `ENVIRONMENT` / `SENTRY_RELEASE`
before the app is created.

**Structured logs** — `cw_logging` emits JSON when `JSON_LOGS=1`.

Whatever you add, remember that per-conversation diagnostics belong in interaction events
([chapter 6](06-events-in-interactions.md)), not only in logs. Operators can read events; they usually
cannot read your logs.

## Security

- **Rotate `API_KEYS`** if it ever leaks, and never commit one. The template ships no real keys.
- **Settings are secrets.** `ExampleCredentials.api_token` is stored in plain text in the database and
  returned by `GET /api/example_credentials`. Restrict who can reach the configuration page, and
  consider returning a masked value once you store something genuinely sensitive.
- **Never log tokens**, and never write them into interaction events.
- **Keep dependencies current.** The configuration page runs inside the platform's own page, not in an
  iframe sandbox.

---

**Next:** [14. Advanced](14-advanced.md) — streaming and local modules.
