# Reference: glossary

The same thing often has one name in the code, another in the Daktela AI admin, and a third in conversation.
This table is the translation.

| Term | What it is |
|---|---|
| **Addon** | An HTTP service you host that extends bot-platform. This repository is one. |
| **Manifest** | `GET /manifest` — everything the platform knows about your addon. Generated from your catalog classes. |
| **Module** | A node the flow designer drags onto the builder canvas. One `Module` subclass in `server/modules/catalog/`. |
| **Proxy module** | What bot-platform calls your module internally, once it has copied it into its `proxy_modules` table. Same thing, platform-side name. |
| **Integration** | A function the AI agent can call on its own (`type: function`). A `widget` type exists in the SDK but the platform cannot render it yet. |
| **Dynamic list** | A searchable option list the builder queries while the designer types. |
| **Configuration page** | Your React UI rendered in the platform's admin interface, mounted via `mountConfiguration`. |
| **Discussion** | One conversation. What your module receives as `self.discussion`. |
| **Interaction** | The same conversation, as labelled in the Daktela AI admin. The Events panel lives on its detail screen. |
| **Discussion event** | A row in `discussion_events`. What `add_debug_info` produces. |
| **Action** | One instruction in a module's response: send a message, set a context, take a port. |
| **Context** | Variables scoped to one flow run. |
| **Store** | Variables scoped to the whole conversation. |
| **Output port** | An arrow leaving a node. Your module picks one per execution. |
| **Output context** | A declaration that the module sets a given context variable, so later nodes can offer it. |
| **Tenant** | One bot-platform instance. Identified by `(customer, instance_id)`. |
| **Instance** | A bot-platform deployment/environment an addon can be activated for. |
| **Customer** | The environment identifier in the `X-Customer` header — part of the tenant key, not an end user. |
| **Custom addon** | An addon registered by pasting its URL into the Daktela AI admin. How third-party and local addons connect. |
| **Catalog addon** | An addon imported automatically from Daktela's central addons catalog. First-party only. |
| **Catalog** (in this repo) | One of the three scanned directories: `modules/catalog`, `integrations/catalog`, `dynamic_lists/catalog`. |
| **Executor** | A plain helper class a module delegates its logic to. Not scanned, not registered. |
| **`ModuleExecutor`** | The SDK base class that collects actions and builds the response. |
| **Manifest signature** | An HMAC proving an addon is first-party. Third-party addons omit it and are treated as third-party — which is fine. |
| **Module Federation** | The mechanism that lets bot-platform load your React bundle into its own page without an iframe. |
| **`cw_addons`** | The Python SDK. Provides the base classes, catalog discovery, route generation and API-key security. |
| **Bot type** | `chatbot`, `voicebot`, `emailbot` or `rbm`. A module can restrict itself with `enabled_types`. |
| **`LangString`** | A localised string, `LangString(en=..., cs=...)`. Used for every label the builder shows. |
