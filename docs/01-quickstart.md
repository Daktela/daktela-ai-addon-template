# 1. Quickstart

Get the addon running on your machine in about five minutes. No Docker, no database, no bot-platform
yet.

## Requirements

| Tool | Version | Why |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | 0.5+ | installs Python and dependencies |
| Python | 3.13+ | uv installs it for you if missing |
| Node.js | 20.19+, 22.12+ or 24+ | only for the configuration page (the `full` profile) |
| pnpm | 10+ | via `corepack enable` |

## Install and run

```bash
git clone <your fork of this repository>
cd daktela-ai-addon-template

uv sync --all-extras
uv run uvicorn server.main:app --reload
```

The addon is now listening on <http://localhost:8000>.

> `uv sync` pulls the addon SDK (`cw-addons`, `cw-utils`, `cw-database`, `cw-logging`) from a public
> Google Artifact Registry declared in `pyproject.toml`. It is readable anonymously — no login.

## Verify

**1. The manifest.** This is the single most important endpoint: it is what bot-platform reads to
learn what your addon can do.

```bash
curl -H "X-Api-Key: default" http://localhost:8000/manifest
```

```json
{
  "code": "example",
  "name": "Example Addon",
  "version": "1.0.0",
  "modules": [
    { "name": "hello_world", "public": true, "...": "..." },
    { "name": "exchange_rate", "public": true, "...": "..." },
    { "name": "interaction_event", "public": true, "...": "..." },
    { "name": "email_draft", "public": true, "...": "..." },
    { "name": "tenant_settings", "public": true, "...": "..." },
    { "name": "streaming_echo", "public": true, "supports_streaming": true },
    { "name": "local_tag", "public": true, "execution": "local" }
  ],
  "integrations": [{ "name": "order_lookup", "type": "function" }]
}
```

> **The `X-Api-Key` header is not optional.** Without it every endpoint answers `403 Could not
> validate API KEY`. When `API_KEYS` is not set the SDK accepts exactly one key, the literal string
> `default`. This trips up nearly everyone the first time they connect an addon to the platform —
> see [chapter 3](03-connect-to-bot-platform.md).

**2. Health.**

```bash
curl http://localhost:8000/readiness
# {"status":"healthy","backend":"json"}
```

`backend: json` means the addon is storing its settings in memory — the default. There is nothing
else to install. [Chapter 11](11-persistence.md) shows how to switch to Postgres.

**3. Run a module without a bot.** Modules are plain HTTP endpoints, so you can call one directly.

The four `X-` headers besides the key are the tenant: the platform sends them on every call to say
which instance is asking ([reference](reference/http-api.md)). Calling by hand, they only have to be
present and well-formed. `https://your-instance.bot.daktela.com` is the shape a Daktela AI instance
URL takes; substitute your own, and when you are just calling a module by hand nothing has to be
listening there at all.

```bash
curl -X POST http://localhost:8000/module/v1/execute/hello_world \
  -H "X-Api-Key: default" \
  -H "X-Customer: local-dev" \
  -H "X-Bot-Url: https://your-instance.bot.daktela.com" \
  -H "X-Instance-Id: 1" \
  -H "X-Instance-Name: local" \
  -H "Content-Type: application/json" \
  -d '{"attributes": {"greeting": "Hello!"}, "discussion": {"messages": [], "sequence": 0}}'
```

```json
{
  "actions": [
    { "type": "message", "text": "Hello!", "buttons": [] },
    { "type": "context", "contexts": [{ "name": "greeting_sent", "value": "Hello!" }] },
    { "type": "output_port", "name": "done" }
  ],
  "debug": [],
  "sequence": 1
}
```

That is the entire runtime contract: bot-platform sends the flow designer's `attributes` plus the
current `discussion`, and your module answers with a list of actions.

**4. Interactive docs.** Open <http://localhost:8000/> for Swagger UI covering every route.

## The configuration page (the `full` profile)

The addon you just started runs in the `full` profile, which includes a configuration page. An addon
that has nothing for an operator to configure runs `ADDON_PROFILE=basic` instead and needs none of
what follows — see [chapter 13](13-deployment.md).

```bash
corepack enable
cd frontend
pnpm install
pnpm dev
```

Open the URL Vite prints. You get the addon's settings page on its own, with the dev server faking
the headers bot-platform would normally inject. See [chapter 10](10-configuration-page.md).

## Run the checks

```bash
make check     # ruff + pyright + pytest + eslint + tsc + vitest
```

Everything should pass on a fresh clone. If it does not, that is a bug in the template — please open
an issue.

---

**Next:** [2. Project tour](02-project-tour.md) — what every directory in here is for.
