# Developer guide

How to build an addon for the **Daktela AI** bot platform, using this repository as the starting
point.

Read 1–6 in order the first time. After that, use it as a reference.

## Getting started

| # | Chapter | You will |
|---|---|---|
| 1 | [Quickstart](01-quickstart.md) | Run the addon locally, with no Docker and no database |
| 2 | [Project tour](02-project-tour.md) | Learn what every directory does and where your code goes |
| 3 | [Connect to bot-platform](03-connect-to-bot-platform.md) | Register your local addon with the platform |

## Building things

| # | Chapter | You will |
|---|---|---|
| 4 | [Your first module](04-your-first-module.md) | Understand a module, then write one |
| 5 | [Using a module in the builder](05-module-in-the-builder.md) | Get it onto the flow canvas |
| 6 | [Events in interactions](06-events-in-interactions.md) | **Prove your addon ran** |
| 7 | [Calling external APIs](07-calling-external-apis.md) | Handle timeouts and failures properly |
| 8 | [Integrations and tool calls](08-integrations-and-tool-calls.md) | Expose a tool the AI agent can call |
| 9 | [Dynamic lists](09-dynamic-lists.md) | Back a searchable select with live data |
| 10 | [The configuration page](10-configuration-page.md) | Ship a settings UI inside the platform |

## Running it for real

| # | Chapter | You will |
|---|---|---|
| 11 | [Persistence](11-persistence.md) | Turn on Postgres when you need it |
| 12 | [Testing](12-testing.md) | Test modules without a browser or a bot |
| 13 | [Deployment](13-deployment.md) | Ship it |

## Advanced

| # | Chapter | You will |
|---|---|---|
| 14 | [Streaming and local modules](14-advanced.md) | Stream an answer as it is produced, or have the platform run a node itself |

## Reference

- [The addon manifest](reference/manifest.md) — every option in the `Settings(...)` block
- [Input attributes](reference/attributes.md) — all ten types, their fields and gotchas
- [What an addon returns](reference/actions.md) — actions, events and the other response shapes
- [Environment variables](reference/env-vars.md) — every variable and its default
- [HTTP API](reference/http-api.md) — every route, request and response shape
- [Glossary](reference/glossary.md) — the same concept's three different names
- [Troubleshooting](troubleshooting.md) — symptom → cause → fix

## If you read only one thing

An addon is an HTTP service that answers `GET /manifest` with a description of what it can do, and
then answers `POST /module/v1/execute/{name}` when the platform wants it done. Everything else in
this guide is detail.
