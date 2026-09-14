# Troubleshooting

Symptom → cause → fix, in roughly the order you will hit them.

## Starting the addon

| Symptom | Cause | Fix |
|---|---|---|
| `uv sync` cannot find `cw-addons` | The index in `pyproject.toml` was removed or edited | Restore the `[[tool.uv.index]]` block. The registry is public; no credentials needed. |
| `uv sync` sends a stale auth token | A `~/.npmrc` or keyring credential for that registry has expired | Remove the stale entry, or install with a clean user config. Anonymous access works. |
| Startup fails in the catalog loader | Two `Module` subclasses in one file, or an import error inside a catalog file | One class per file; read the traceback — it names the file. |
| `ValueError: No valid database connection string` | Something resolved the Postgres branch without `db_*` set | Check `SETTINGS_STORE` is not set to `postgres`. `unit_tests/test_di.py` guards this. |
| `InterfaceError: Psycopg cannot use the 'ProactorEventLoop'` | Windows, with persistence on | The selector-policy guard in `server/main.py` was removed — restore it. |

## Authentication

| Symptom | Cause | Fix |
|---|---|---|
| Every endpoint returns `403 Could not validate API KEY` | No `X-Api-Key`, or a value not in `API_KEYS` | Send `X-Api-Key: default` (or whatever `API_KEYS` is set to). |
| The platform's **Test** button fails, addon logs a 403 | Custom addons get no auth header unless you configure one | In the Daktela AI admin set custom header `X-Api-Key` / `default`. See [chapter 3](03-connect-to-bot-platform.md). |
| Routes return 422 instead of 403 | Tenant headers are missing, and FastAPI validates them first | Send `X-Customer`, `X-Bot-Url`, `X-Instance-Id`, `X-Instance-Name`. |

## Connecting to bot-platform

| Symptom | Cause | Fix |
|---|---|---|
| Test fails with nothing in the addon log | The platform cannot reach the URL | It has to be publicly reachable — a `localhost` URL never is. Check your tunnel ([chapter 3](03-connect-to-bot-platform.md)). |
| The addon worked yesterday and is now unreachable | A development tunnel was closed, or its URL changed on restart | Restart the tunnel and update the addon's URL in the platform — or deploy it properly ([chapter 13](13-deployment.md)). |
| Test fails with a validation error | A malformed manifest | `curl -H "X-Api-Key: default" localhost:8000/manifest \| jq` and look for a module missing a required field. |
| The addon shows as "not configured" | `GET /instance-configured` answers 409 | Save something on the settings page, or change `_check_configured` in `server/app.py`. |
| The addon activates but nothing happens | It was never activated *for that instance* | Activation is per instance, not global. |
| Activation is refused: "not configured" | `/instance-configured` answers 409 and nothing can clear it | Either save settings on the configuration page, or run the `basic` profile, which does not register the route at all. |
| The addon refuses to start, naming `ADDON_PROFILE` | A typo in the value | Use `full` or `basic`. The check is strict on purpose: a silent fallback would surface as blocked activation instead. |

## Modules

| Symptom | Cause | Fix |
|---|---|---|
| Not in the module selection | `public` is `False` (the default) | `public = True`, restart, re-sync the addon. |
| Changed a module, the builder shows the old one | Its `version` did not change | Bump the module's `version`. The platform updates a known module only when its version changes. |
| Not in the module selection, `public` is true | The platform has a stale manifest | Re-sync the addon from the Addons page, or wait for the scheduled sync. |
| Not in `/manifest` either | Wrong directory, or the addon did not restart | It must be a `.py` file directly in `server/modules/catalog/`. |
| The flow stops at the node | No `output_ports`, or no `add_output_port` on that path | Declare a port and take one on **every** path through `execute()`. |
| The flow takes a port called `other` | `execute()` raised | Look at the Events panel: the SDK recorded the exception as an error event. |
| An attribute is always empty | `input_attributes` name ≠ pydantic field name | Make them identical. |
| The addon will not start after adding a select | `default_value` is not one of the options | Use one of the option keys. |
| An existing flow lost its node | A published module's `name` was renamed | Restore the old name; add a new module instead of renaming. |

## Events

| Symptom | Cause | Fix |
|---|---|---|
| No event in the Events panel | The module never ran | Check the addon log for `Executing module ...`. |
| Still nothing | The module ran but wrote no debug entry | Call it directly and inspect `debug` in the response. |
| Only error events from the platform | The platform could not reach or parse your response | Read the error event's message — it carries the HTTP status or exception. |
| Events appear under a different conversation | You are looking at the wrong one | Use the instance-wide view `GET /api/:instanceId/discussion-events`. |

## The configuration page

| Symptom | Cause | Fix |
|---|---|---|
| No "Configure" button on the addon card | You are running the `basic` profile | `curl <addon>/liveness` to confirm, then deploy the full image if you meant to have a page. |
| The page looks nothing like the platform | The shared theme is not applied | `import { theme } from '@coworkers/cw-utils'` and wrap the app in `ThemeProvider` — see [chapter 10](10-configuration-page.md). |
| Headings are enormous | The shared theme does not resize MUI's heading variants | Use `variant="h5" component="h1"` rather than `variant="h1"`. |
| `pnpm install` 403s on `@coworkers/...` | A stale credential for that registry in your `~/.npmrc` | The registry is anonymous; remove the stale entry. |
| Blank page inside the platform | The bundle failed to load | Check `/dist/assets/addonBundle.js` is 200 on the addon's public URL. Build it: `make frontend-build`. |
| The settings form stays empty and nothing errors | The backend is running the `basic` profile: `/api/example_credentials` 404s, which also means "nothing saved yet" | `curl <backend>/liveness` — it reports the profile. |
| `make orval` fails against a running backend | The backend is in the `basic` profile, which does not serve `/openapi-frontend.json` | Run it with `make backend` instead of `make backend-basic`. |
| Every API call 404s | A bare `fetch` or a hard-coded URL | Route everything through `addonAxios`, so `apiBasePath` applies. |
| Works standalone, breaks inside the platform | `apiBasePath` was ignored | `configureAddonApi(apiBasePath)` must run before the first request. |
| The addon's menu does nothing, or leaves the addon | Assigning to `location.hash` overwrites bot-platform's own route | Navigate with `pushHash` from `src/app/browserHash.ts`, which nests under `routerBasePath` |
| Navigating breaks the Daktela AI admin | Path-based routing | Use hash routing. |
| `make orval` fails | The backend is not running, or is on another port | Start it; pass `BACKEND_PORT` if it is not 8000. |
| Saving works, the addon stays "not configured" | The check reads a different key than the route writes | Both must use `TenantKey(customer, instance_id)`. |

## Persistence

| Symptom | Cause | Fix |
|---|---|---|
| `/readiness` says `backend: json` after enabling Postgres | Not all five `db_*` variables are set | All five are required. Check for typos — the prefix is lowercase. |
| `/readiness` returns 503 | The database is unreachable | `make db-up`; check the port (the dev database is on **5442**). |
| `alembic upgrade head` cannot connect | A different Postgres is listening on that port | Check `docker ps`, and the port in `docker-db/docker-compose.yaml`. |
| `relation "example_credentials" does not exist` | Migrations were never applied | `make migrate`. |
| The process exits after repeated database errors | `CWSessionPool` sends itself SIGTERM after 30 consecutive failures | Intentional. Fix the database; the orchestrator restarts the pod. |
| Settings vanish on restart | The JSON store with no `ADDON_SETTINGS_FILE` | Set it, or switch to Postgres. |
| Two replicas disagree about settings | The JSON store is per-process | Switch to Postgres. |

## Tests and CI

| Symptom | Cause | Fix |
|---|---|---|
| Tests hit a real database | A local `.env` with `db_*` | `unit_tests/conftest.py` strips those; make sure the autouse fixture is still there. |
| `ruff format --check` fails in CI, passes locally | Formatting was never applied | `make format`. |
| pyright fails on a SQLModel table | `__tablename__` typing quirk | The template pins it with a narrow `pyright: ignore`. |
| Frontend install fails in CI | A stale lockfile | `pnpm install` locally and commit `pnpm-lock.yaml`. |

## Still stuck

1. `curl -H "X-Api-Key: default" localhost:8000/manifest | jq` — is the addon advertising what you think?
2. The addon's own log — did the request arrive?
3. The interaction's Events panel — what did the platform think happened?
4. Call the endpoint directly with `curl` — does it work without the platform involved?

Those four, in that order, isolate almost everything.
