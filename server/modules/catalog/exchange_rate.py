"""Calling an external HTTP API from a module.

Demonstrates : delegating to an executor, calling a third-party API with a
               timeout, and branching to a success or failure output port.
Documented in: docs/07-calling-external-apis.md
Change first : the API in `server/modules/executors/exchange_rate_executor.py`.

The module class stays declarative - it describes the node and hands the work
to an executor. That split keeps the manifest readable once the business
logic grows past a few lines; `hello_world.py` shows the other extreme.
"""

from typing import override

from cw_addons.modules.models import (
    LangString,
    ModuleResponses,
    NumberAttribute,
    OutputContext,
    OutputPortStatic,
    SelectAttribute,
)
from cw_addons.modules.module import Module
from pydantic import BaseModel

from server.modules.executors.exchange_rate_executor import ExchangeRateExecutor


class ExchangeRateAttributes(BaseModel):
    amount: float
    source_currency: str
    target_currency: str
    timeout_seconds: float


class ExchangeRateModule(Module[ExchangeRateAttributes]):
    attributes: ExchangeRateAttributes

    name = "exchange_rate"
    version = "v1"
    public = True

    icon = "💱"
    category = LangString(en="Examples", cs="Příklady")
    title = LangString(en="Convert Currency", cs="Převod měny")
    short_description = LangString(
        en="Converts an amount using live exchange rates.",
        cs="Převede částku podle aktuálního kurzu.",
    )
    description = LangString(
        en=(
            "Calls the public Frankfurter exchange-rate API and reports the converted amount. "
            "Shows how to handle timeouts and upstream failures without breaking the flow."
        ),
        cs=(
            "Zavolá veřejné API Frankfurter a vrátí převedenou částku. Ukazuje, jak ošetřit "
            "timeouty a chyby cizí služby, aniž by se rozbil tok."
        ),
    )

    _CURRENCIES = [{"CZK": "CZK"}, {"EUR": "EUR"}, {"USD": "USD"}, {"GBP": "GBP"}]

    input_attributes = [
        NumberAttribute(
            name="amount",
            title=LangString(en="Amount", cs="Částka"),
            description=LangString(en="Amount to convert.", cs="Částka k převodu."),
            default_value=100,
            required=True,
        ),
        SelectAttribute(
            name="source_currency",
            title=LangString(en="From", cs="Z měny"),
            description=LangString(en="Currency to convert from.", cs="Zdrojová měna."),
            options=_CURRENCIES,
            default_value="EUR",
            required=True,
        ),
        SelectAttribute(
            name="target_currency",
            title=LangString(en="To", cs="Do měny"),
            description=LangString(en="Currency to convert to.", cs="Cílová měna."),
            options=_CURRENCIES,
            default_value="CZK",
            required=True,
        ),
        # Make the timeout an attribute, not a constant. The flow designer
        # knows how long this node may hold up a live interaction; you do not.
        NumberAttribute(
            name="timeout_seconds",
            title=LangString(en="Timeout (seconds)", cs="Timeout (sekundy)"),
            description=LangString(
                en="How long to wait for the exchange-rate service before taking the timeout port.",
                cs="Jak dlouho čekat na službu s kurzy, než se použije port timeout.",
            ),
            default_value=5,
            required=True,
        ),
    ]

    output_contexts = [
        OutputContext(
            name="converted_amount",
            title=LangString(en="Converted amount", cs="Převedená částka"),
            description=LangString(
                en="The result, for later nodes to use.",
                cs="Výsledek pro použití v dalších uzlech.",
            ),
        ),
    ]

    # Separate ports let the flow designer handle each failure deliberately
    # instead of the flow dead-ending when the upstream API misbehaves.
    # `timeout` is split out from `error` on purpose: it is the one a designer
    # most often wants to route differently - retry, or apologise and move on.
    output_ports = [
        OutputPortStatic(
            name="success",
            title=LangString(en="Success", cs="Úspěch"),
            description=LangString(en="The rate was retrieved.", cs="Kurz byl získán."),
        ),
        OutputPortStatic(
            name="timeout",
            title=LangString(en="Timeout", cs="Timeout"),
            description=LangString(
                en="The service did not answer within the configured timeout.",
                cs="Služba neodpověděla ve stanoveném timeoutu.",
            ),
        ),
        OutputPortStatic(
            name="error",
            title=LangString(en="Error", cs="Chyba"),
            description=LangString(
                en="The service answered, but with an error.",
                cs="Služba odpověděla, ale chybou.",
            ),
        ),
    ]

    @override
    async def execute(self) -> ModuleResponses:
        return await ExchangeRateExecutor(
            discussion=self.discussion,
            attributes=self.attributes,
            tenant=self.tenant,
            module_name=self.name,
        ).run()
