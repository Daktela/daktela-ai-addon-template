"""Business logic for `exchange_rate`.

Executors live outside the catalog directory on purpose: only files in
`server/modules/catalog/` are scanned for modules, so anything here is a plain
class you can import, subclass and unit-test without the framework noticing.
"""

from typing import TYPE_CHECKING, cast

import httpx
from cw_addons.modules.executor import ModuleExecutor
from cw_addons.modules.models import DebugInfoType, ModuleResponses

if TYPE_CHECKING:
    # Type-checking only, so the module -> executor import stays one-way.
    from server.modules.catalog.exchange_rate import ExchangeRateAttributes

API_URL = "https://api.frankfurter.dev/v1/latest"
"""Public, no API key, no rate limit worth worrying about - good for a demo.
Swap this for whatever your addon actually integrates with."""

# The timeout is not a constant here: it comes from the module's
# `timeout_seconds` attribute, so the flow designer decides how long this node
# may hold up a live interaction. See docs/07-calling-external-apis.md.


class ExchangeRateExecutor(ModuleExecutor):
    async def run(self) -> ModuleResponses:
        # `ModuleExecutor.attributes` is a bare BaseModel; narrowing it once
        # here gives the rest of the method type-checked field access.
        attributes = cast("ExchangeRateAttributes", self.attributes)

        amount = attributes.amount
        source = attributes.source_currency.upper()
        target = attributes.target_currency.upper()

        if source == target:
            self._succeed(amount, source, target, amount)
            return self.get_response()

        try:
            rate = await self._fetch_rate(source, target, attributes.timeout_seconds)
        except httpx.TimeoutException:
            # A timeout gets its own port. It is the failure a designer most
            # often wants to treat differently from a bad response.
            self.add_debug_info(
                message=(f"Exchange-rate lookup {source}->{target} timed out after {attributes.timeout_seconds}s"),
                debug_type=DebugInfoType.warning,
            )
            self.add_message("The exchange-rate service is taking too long right now.")
            self.add_output_port("timeout")
            return self.get_response()
        except (httpx.HTTPError, KeyError, ValueError) as error:
            # Record *why* it failed where an operator can find it later, then
            # let the flow continue down the error port. Never re-raise: an
            # unhandled exception costs the flow designer the chance to react.
            self.add_debug_info(
                message=f"Exchange-rate lookup {source}->{target} failed: {error}",
                debug_type=DebugInfoType.error,
            )
            self.add_message("Sorry, I could not reach the exchange-rate service right now.")
            self.add_output_port("error")
            return self.get_response()

        self._succeed(amount, source, target, round(amount * rate, 2))
        return self.get_response()

    async def _fetch_rate(self, source: str, target: str, timeout_seconds: float) -> float:
        # Pass the designer's budget straight to the client. Every await in
        # this method has to fit inside it - httpx enforces that for the
        # request itself; anything else you add here is on you.
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(API_URL, params={"base": source, "symbols": target})
            response.raise_for_status()
            payload = response.json()

        return float(payload["rates"][target])

    def _succeed(self, amount: float, source: str, target: str, converted: float) -> None:
        self.add_debug_info(
            message=f"Converted {amount} {source} to {converted} {target}",
            debug_type=DebugInfoType.info,
        )
        self.add_context("converted_amount", converted)
        self.add_message(f"{amount} {source} is {converted} {target}.")
        self.add_output_port("success")
