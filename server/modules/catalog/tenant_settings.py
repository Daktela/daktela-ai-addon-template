"""Reading the addon's own settings from inside a module.

Demonstrates : dependency injection into a module, and the fact that settings
               saved on the configuration page are readable at flow runtime.
Documented in: docs/10-configuration-page.md
Change first : replace `SettingsStore` with whatever service your module needs.

A `Provide[...]` default argument is how a catalog module reaches anything
from `server/di.py`. `ConfigurationService.wire_container()` in
`server/app.py` is what makes it work even for files loaded dynamically from
a catalog directory.
"""

from typing import override

from cw_addons.modules.executor import ModuleExecutor
from cw_addons.modules.models import (
    LangString,
    ModuleResponses,
    OutputContext,
    OutputPortStatic,
)
from cw_addons.modules.module import Module
from pydantic import BaseModel

from server.di import SettingsStoreProvider
from server.settings.models import TenantKey
from server.settings.store import SettingsStore


class TenantSettingsAttributes(BaseModel):
    """This module takes no input - it reads everything from the tenant."""


class TenantSettingsModule(Module[TenantSettingsAttributes]):
    attributes: TenantSettingsAttributes

    name = "tenant_settings"
    version = "v1"
    public = True

    icon = "⚙️"
    category = LangString(en="Examples", cs="Příklady")
    title = LangString(en="Read Addon Settings", cs="Načtení nastavení addonu")
    short_description = LangString(
        en="Reads the credentials saved on the addon's settings page.",
        cs="Načte údaje uložené na stránce nastavení addonu.",
    )
    description = LangString(
        en=(
            "Looks up the settings stored for the current the platform instance and branches "
            "depending on whether the addon has been configured."
        ),
        cs=(
            "Vyhledá nastavení uložené pro aktuální instanci the platformy a podle toho, zda je "
            "addon nakonfigurovaný, zvolí výstupní port."
        ),
    )

    input_attributes = []

    output_contexts = [
        OutputContext(
            name="addon_display_name",
            title=LangString(en="Configured display name", cs="Nastavený název"),
            description=LangString(
                en="The display name saved on the settings page.",
                cs="Název uložený na stránce nastavení.",
            ),
        ),
    ]

    output_ports = [
        OutputPortStatic(
            name="configured",
            title=LangString(en="Configured", cs="Nakonfigurováno"),
            description=LangString(
                en="Credentials were found for this instance.",
                cs="Pro tuto instanci byly nalezeny údaje.",
            ),
        ),
        OutputPortStatic(
            name="not_configured",
            title=LangString(en="Not configured", cs="Nenakonfigurováno"),
            description=LangString(
                en="Nobody has filled in the settings page yet.",
                cs="Stránka nastavení zatím nebyla vyplněna.",
            ),
        ),
    ]

    @override
    async def execute(self, store: SettingsStore = SettingsStoreProvider) -> ModuleResponses:
        executor = ModuleExecutor(
            discussion=self.discussion,
            attributes=self.attributes,
            tenant=self.tenant,
            module_name=self.name,
        )

        # `self.tenant` is built from the headers the platform sends with every
        # module execution, so a module always knows which instance it runs for.
        credentials = await store.get(TenantKey(customer=self.tenant.customer, instance_id=self.tenant.instance_id))

        if credentials is None:
            executor.add_message("This addon has not been configured for your instance yet.")
            executor.add_output_port("not_configured")
            return executor.get_response()

        executor.add_context("addon_display_name", credentials.display_name)
        executor.add_message(f"Configured as: {credentials.display_name}")
        executor.add_output_port("configured")
        return executor.get_response()
