# Reference: environment variables

Every variable has a working default, so an empty environment is a valid configuration. Copy
`.env.example` to `.env` to change any of them.

## Security

| Variable | Default | Read by | Notes |
|---|---|---|---|
| `API_KEYS` | `default` | `cw_addons.security` | Comma-separated list of accepted `X-Api-Key` values. **Set this in production.** With it unset, the literal string `default` is the only valid key. |
| `COWORKERS_PRIVATE_KEY` | a placeholder | `cw_addons.models.Settings` | HMAC key for the manifest signature. Only relevant to first-party signed addons; third-party addons omit the signature. |

## Profile

| Variable | Default | Read by | Notes |
|---|---|---|---|
| `ADDON_PROFILE` | `full` | `server/profile.py` | `full` or `basic`. `basic` drops the configuration page: no `/api/example_credentials`, no `/openapi-frontend.json`, no `/dist`, and **no `GET /instance-configured`**. An unrecognised value refuses to start rather than falling back. |

## Addon identity

Defaults live in `server/identity.py`; these override them, so one image can
serve several environments. See [the manifest reference](manifest.md).

| Variable | Default | Read by | Notes |
|---|---|---|---|
| `ADDON_CODE` | `example` | `server/identity.py` | The stable identifier. Change it once when you fork, never afterwards. |
| `ADDON_NAME` | `Example Addon` | ″ | Display name on the addon card. |
| `ADDON_DESCRIPTION` | see the file | ″ | Shown on the card. |
| `ADDON_VERSION` | `1.0.0` | ″ | Also busts the configuration page's bundle cache. CI can inject a git tag here. |
| `ADDON_AUTHOR` | `Your Company` | ″ | |
| `ADDON_FA_ICON` | `puzzle-piece` | ″ | Font Awesome icon name, no `fa-` prefix. |
| `ADDON_BASE64_ICON` | unset | ″ | A full `data:image/png;base64,…` URI. Wins over `ADDON_FA_ICON`. Long values belong in `server/identity.py` rather than an env var. |
| `ADDON_COLOR` | `#2c6fbb` | ″ | Accent colour. |
| `ADDON_URL` | — | `cw_addons` | The addon's public URL, used when generating the manifest signature. |
| `ROOT_PATH` | `""` | `server/app.py` | Set when a reverse proxy serves the addon under a path prefix, so the generated OpenAPI URLs stay correct. |

## Settings storage

| Variable | Default | Read by | Notes |
|---|---|---|---|
| `SETTINGS_STORE` | auto-detected | `server/di.py` | `json` or `postgres`. Overrides the `db_*` detection. |
| `ADDON_SETTINGS_FILE` | — | `server/di.py` | Path the JSON store mirrors to. Unset means pure in-memory. |
| `db_host` | — | `cw_utils.DBConnectionSettings` | |
| `db_port` | — | ″ | The bundled dev database uses **5442**. |
| `db_name` | — | ″ | |
| `db_username` | — | ″ | |
| `db_password` | — | ″ | |
| `db_ssl` | — | ″ | |
| `db_extra_url_args` | — | ″ | Appended to the connection string. |

All five of `db_host`, `db_port`, `db_name`, `db_username`, `db_password` must be present for the
addon to switch to Postgres. The prefix is lowercase `db_` — that is what `pydantic-settings` looks
for.

## Local development

| Variable | Default | Read by | Notes |
|---|---|---|---|
| `BACKEND_PORT` | `8000` | Makefile, `vite.config.ts`, `orval.config.ts` | Keeps the backend, the frontend proxy and codegen pointing at the same port. |

## Observability (not wired up by default)

The template ships without tracing or error reporting. These are the variables the underlying
libraries already understand if you add them — see [chapter 13](../13-deployment.md).

| Variable | Read by |
|---|---|
| `OTEL_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME` | `cw_utils.otel` |
| `METRICS_ENABLED`, `EXPOSE_METRICS`, `METRICS_PORT` | `cw_utils.otel` |
| `SENTRY_DSN`, `ENVIRONMENT`, `SENTRY_RELEASE` | `sentry-sdk` |
| `JSON_LOGS`, `CW_LOGGER_DEFAULT_LEVEL`, `CW_LOGGER_MODULE_LEVELS` | `cw_logging` |

## Headers, not variables

These arrive per request from bot-platform and are not configured anywhere:

| Header | Meaning |
|---|---|
| `X-Api-Key` | Authentication |
| `X-Customer` | Environment identifier — part of the tenant key |
| `X-Instance-Id` | Instance id — part of the tenant key |
| `X-Instance-Name` | Instance display name |
| `X-Bot-Url` | The instance's base URL |
| `X-Discussion-Id`, `X-Message-Id`, `X-User-Token`, `X-Request-Id` | Correlation - which conversation, message and request this call belongs to |
