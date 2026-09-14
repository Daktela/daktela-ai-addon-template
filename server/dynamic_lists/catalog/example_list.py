"""Backing a `DynamicListAttribute` with searchable options.

Demonstrates : a dynamic list - the builder queries it while the flow designer
               types, so the options do not have to be known up front.
Documented in: docs/09-dynamic-lists.md
Change first : replace `DEPARTMENTS` with a lookup against your own system.

Bot-platform calls `POST /dynamic_list/v1/example_list` with a search query,
a page and a limit, and gives up after 10 seconds - do the paging and
filtering here, never return an unbounded list.
"""

from typing import override

from cw_addons.dynamic_selects.dynamic_select import (
    DynamicItem,
    DynamicList,
    DynamicListRequest,
    DynamicListResponse,
)

DEPARTMENTS = [
    "Billing",
    "Customer Care",
    "Field Service",
    "Logistics",
    "Onboarding",
    "Retention",
    "Sales",
    "Technical Support",
]


class ExampleList(DynamicList):
    name = "example_list"
    attributes: DynamicListRequest

    @override
    async def execute(self) -> DynamicListResponse:
        query = (self.attributes.query or "").strip().casefold()

        matches = [name for name in DEPARTMENTS if query in name.casefold()]
        matches.sort()

        start = (self.attributes.page - 1) * self.attributes.limit
        page = matches[start : start + self.attributes.limit]

        return DynamicListResponse(
            items=[DynamicItem(value=name.lower().replace(" ", "_"), label=name) for name in page]
        )
