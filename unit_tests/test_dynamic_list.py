"""The builder calls this while the flow designer types."""

from cw_addons.dynamic_selects.dynamic_select import DynamicListRequest
from cw_addons.utils.test_helpers import dummy_tenant

from server.dynamic_lists.catalog.example_list import ExampleList


async def _search(query: str = "", limit: int = 50, page: int = 1) -> list[str]:
    listing = ExampleList(
        attributes=DynamicListRequest(query=query, limit=limit, page=page),
        tenant=dummy_tenant,
    )
    response = await listing.execute()
    return [item.label for item in response.items]


async def test_returns_everything_for_an_empty_query() -> None:
    assert len(await _search()) == 8


async def test_filters_case_insensitively() -> None:
    assert await _search("SUPPORT") == ["Technical Support"]


async def test_pages() -> None:
    first = await _search(limit=3, page=1)
    second = await _search(limit=3, page=2)

    assert len(first) == 3
    assert len(second) == 3
    assert set(first).isdisjoint(second)
