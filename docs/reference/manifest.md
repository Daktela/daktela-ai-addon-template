# Reference: the addon manifest

Everything the platform knows about your addon comes from `GET /manifest`, and everything in that
manifest comes from the `Settings(...)` block in `server/app.py`. This page lists every field.

The identity half of it lives in `server/identity.py` - that is the file you
edit when you fork:

```python
class AddonIdentity(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ADDON_")

    code: str = "example"
    name: str = "Example Addon"
    version: str = "1.0.0"
    ...
```

Every field is also overridable by an `ADDON_`-prefixed environment variable,
so one image can serve several environments - a staging deployment can call
itself "Example Addon (staging)", and CI can inject the version from a git
tag, without a rebuild.

`server/app.py` then feeds that identity, plus the catalog paths and the
profile's `has_setting`, into the SDK's `Settings(...)`. The catalog paths stay
in `app.py` because they describe the repository's layout rather than the
addon.

## Identity

| Field | Required | What it does |
|---|---|---|
| `code` | ✔ | **The addon's stable identifier.** Unique per platform; stored against every activation and every module row, and shown beside every event your modules write (`<module>::<code>`). Pick it once and never change it — changing it makes the platform treat your addon as a different, new one. |
| `name` | ✔ | Display name on the addon card and detail page. |
| `description` | ✔ | One or two sentences, shown on the card. |
| `version` | ✔ | Free-form string, e.g. `"1.0.0"`. The platform appends it to the bundle URL, so bumping it also busts the browser cache for your configuration page. |
| `author` | ✔ | Shown on the card. |
| `root_path` | ✔ | Always `__file__`. The catalog paths below are resolved relative to the directory containing it. |

## Where your code lives

| Field | What it does |
|---|---|
| `module_catalog_path` | Directory scanned for `Module` subclasses — one per file. |
| `integration_catalog_path` | Same, for `Integration` subclasses. |
| `dynamic_list_catalog_path` | Same, for `DynamicList` subclasses. |

All three are optional: omit one and that capability is simply absent. Each is a single directory —
the SDK does not merge several, and calling the registration twice clears the first result.

## Presentation

| Field | What it does |
|---|---|
| `fa_icon` | A Font Awesome icon name without the `fa-` prefix, e.g. `"puzzle-piece"`. |
| `base64_icon` | Your own 48×48 icon as a **full data URI** — `data:image/png;base64,…` — because the admin puts it straight into a CSS `url(...)`. |

Both may be set: the platform uses `base64_icon` when it is present and falls back to `fa_icon`
otherwise. Ship a Font Awesome name as the default and add the bitmap once you have artwork.
| `color` | Accent colour, e.g. `"#2c6fbb"`. Also tints your module nodes in the builder page. |
| `tags` | Free-form strings for grouping in the addon list. |

## Capability flags

| Field | Default | What it does |
|---|---|---|
| `has_setting` | `False` | Whether the addon has a configuration page. **This only puts the "Configure" button on the addon's card** — it does not gate the route, so an operator reaching the detail URL directly still makes the platform try to load your bundle. In this template it follows `ADDON_PROFILE` (see [chapter 13](../13-deployment.md)). |
| `has_widgets` | `False` | Reserved for chat-window widgets. **Nothing in the platform reads it yet** — leave it alone, and do not declare `widget`-type integrations ([chapter 8](../08-integrations-and-tool-calls.md)). |
| `enabled_instance_types` | `[]` | Restrict to `chatbot`, `voicebot`, `emailbot`, `rbm`. Empty means all of them. If it excludes an instance's type, the addon syncs but never appears for that instance. |

## Activation lifecycle

| Field | Default | What it does |
|---|---|---|
| `auto_activate` | `False` | Activate on every instance as soon as the addon syncs, instead of waiting for an operator. Also the flag that makes the platform call `POST /api/register_addon`. For a template, `False` is the right default: activation stays an explicit decision. |
| `allow_manual_activation` | `True` | Whether the "Activate" button appears. With this `False` **and** `auto_activate` `False`, nobody can ever activate the addon. |

The lifecycle routes themselves are not manifest fields — they appear because you passed callbacks to
`LifecycleService.register`. One of them has a sharp edge:

> **`GET /instance-configured` answering 409 blocks activation.** The platform refuses to activate an
> addon that says it is not configured. If your addon has no configuration page, do not register the
> route at all: an absent route 404s, which the platform reads as "nothing to configure here". This is
> exactly why the `basic` profile omits the callback.

## Fields the platform overrides

Set these and nothing happens — unless your addon is first-party and signed:

| Field | What the platform does with a third-party addon |
|---|---|
| `allow_deactivation` | Forced to `True`. An operator can always deactivate your addon. |
| `allow_removal` | Forced to `True`. An operator can always remove it. |
| `sidebar_position` | Forced to `null`. |
| `sidebar_section` | Forced to `null`. |
| `sidebar_label` | Unused without a position. |

In other words a third-party addon appears as a card in the addon list, never as its own entry in the
platform's left sidebar, and can always be turned off. Do not bother setting these four.

## Signing

`signature` is how the platform recognises a **first-party** addon — one published by Daktela itself,
which is what unlocks the sidebar fields and the deactivation locks above. It is an HMAC over the
addon's code and URL, keyed by a secret only first-party builds have.

Third-party addons simply omit it, which is the correct and supported thing to do: everything in this
guide works without a signature. Producing one is out of scope here.

## The generated manifest

Your `Settings` plus the scanned catalogs:

```json
{
  "code": "example",
  "name": "Example Addon",
  "version": "1.0.0",
  "author": "Your Company",
  "has_setting": true,
  "has_widgets": false,
  "auto_activate": false,
  "enabled_instance_types": [],
  "modules": [{ "name": "hello_world", "public": true, "...": "..." }],
  "integrations": [{ "name": "order_lookup", "type": "function" }]
}
```

`GET /manifest` is ETag-cached and built **once at startup**, so a manifest change needs an addon
restart *and* a re-sync on the platform side — see [chapter 5](../05-module-in-the-builder.md).
