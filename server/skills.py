from cw_addons.modules.models import Tenant
from cw_addons.skills import AddonSkill


async def get_skills(tenant: Tenant) -> list[AddonSkill]:
    return [
        AddonSkill(
            key="order_status",
            name="Order status",
            load_when="The customer asks about an order or its delivery.",
            instructions="Ask for the order number if it is missing. Use order_lookup and explain its returned status without inventing delivery dates.",
            tools=["order_lookup"],
        )
    ]
