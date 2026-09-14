# 9. Dynamic lists

A `SelectAttribute` needs its options known when you write the module. A **dynamic list** does not:
the builder queries your addon while the flow designer types.

Use one whenever the options come from a system that changes — queues, agents, departments, product
categories, mailboxes.

Worked example: `server/dynamic_lists/catalog/example_list.py`.

## Declaring the list

```python
class ExampleList(DynamicList):
    name = "example_list"
    attributes: DynamicListRequest          # query, limit, page

    async def execute(self) -> DynamicListResponse:
        ...
        return DynamicListResponse(items=[DynamicItem(value="sales", label="Sales")])
```

One class per file in `server/dynamic_lists/catalog/`, discovered at startup like everything else.

`value` is what gets stored in the flow; `label` is what the designer sees. Keep `value` stable — it
is saved inside flows, so changing it later breaks them, exactly like renaming a module.

## Using it from a module

```python
DynamicListAttribute(
    name="department",
    title=LangString(en="Department", cs="Oddělení"),
    description=LangString(en="Which department to route to.", cs="..."),
    multi_select=False,       # True gives the designer a multi-select
    required=True,
)
```

The attribute's `name` is the field in your pydantic attributes model. With `multi_select=True` the
value is a list of strings instead of a string.

> The link between the attribute and the list is **by name**: bot-platform asks the addon for a list
> whose `name` matches. Keep them in sync.

## Honour query, limit and page

```python
query = (self.attributes.query or "").strip().casefold()

matches = [name for name in DEPARTMENTS if query in name.casefold()]
matches.sort()

start = (self.attributes.page - 1) * self.attributes.limit
return DynamicListResponse(items=[... for name in matches[start : start + self.attributes.limit]])
```

Three rules:

1. **Filter server-side.** The builder does not filter for you.
2. **Page.** Returning ten thousand items makes the select unusable and the request slow.
3. **Answer within 10 seconds.** That is the platform's timeout; past it the designer sees an empty
   list with no explanation. If your upstream is slow, cache.

Matching should be forgiving: case-insensitive, and diacritics-insensitive if your labels have any.
A designer typing `cerny` should find `Černý`.

```python
import unicodedata

def normalise(text: str) -> str:
    lowered = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in lowered if unicodedata.category(c) != "Mn")
```

## Per-tenant lists

`self.tenant` is available, so the list can differ per bot-platform instance:

```python
class QueueList(DynamicList):
    name = "queue_list"

    async def execute(self) -> DynamicListResponse:
        credentials = await store.get(
            TenantKey(customer=self.tenant.customer, instance_id=self.tenant.instance_id)
        )
        if credentials is None:
            return DynamicListResponse(items=[])     # not configured yet - empty, not an error
        ...
```

Return an empty list rather than raising when the addon is not configured. The designer gets an empty
select, which is confusing but survivable; an exception gets them nothing and an error in the console.

## Calling it directly

```bash
curl -X POST localhost:8000/dynamic_list/v1/example_list \
  -H "X-Api-Key: default" -H "X-Customer: local" -H "X-Bot-Url: https://your-instance.bot.daktela.com" \
  -H "X-Instance-Id: 1" -H "X-Instance-Name: local" \
  -H "Content-Type: application/json" \
  -d '{"query": "sup", "limit": 10, "page": 1}'
```

```json
{ "items": [{ "value": "technical_support", "label": "Technical Support" }] }
```

Bot-platform reaches it through its own route,
`GET /api/addon/:id/dynamic-list/:listName?instanceId=…&query=…`, which proxies to the above.

---

**Next:** [10. The configuration page](10-configuration-page.md).
