"""A module the platform runs itself, without calling this addon at all.

Demonstrates : `LocalModule` - `execution = "local"` plus `local_actions`.
Documented in: docs/14-advanced.md
Change first : the `local_actions` list.

**Advanced, and deliberately limited.** A local module declares what it wants
done in the manifest; the platform interprets that declaration itself, so the
node costs no network round trip and keeps working while this addon is down or
being redeployed. The price is that it cannot run code: no HTTP calls, no
database, no branching. It can set context variables and sender metadata from
its own attributes, and that is all.

Use it for the small stateless nodes that would otherwise pay a round trip to
do nothing - tagging an interaction, stamping a constant, copying one attribute
into a context variable.

**Local modules pair naturally with dynamic lists.** Give one a
`DynamicListAttribute` and the flow designer picks a real value from your system
- a queue, a department, a product category - while building the flow. That
lookup runs on your addon at *design* time only; at *run* time the node is pure
platform, so you get an always-current picker and a node that costs nothing to
execute. See docs/09-dynamic-lists.md.

The `{placeholder}` syntax below is substituted by the platform from this
node's attributes.
"""

from cw_addons.modules.local_module import LocalModule
from cw_addons.modules.models import (
    LangString,
    LocalContextAction,
    LocalSenderMetadataAction,
    OutputPortStatic,
    StringAttribute,
)
from pydantic import BaseModel


class LocalTagAttributes(BaseModel):
    tag: str
    source: str


class LocalTagModule(LocalModule[LocalTagAttributes]):
    attributes: LocalTagAttributes

    name = "local_tag"
    version = "v1"
    public = True

    icon = "🏷️"
    category = LangString(en="Examples", cs="Příklady")
    title = LangString(en="Tag Conversation (local)", cs="Označení konverzace (lokální)")
    short_description = LangString(
        en="Stamps a tag onto the conversation without calling the addon.",
        cs="Označí konverzaci, aniž by volal addon.",
    )
    description = LangString(
        en=(
            "Runs inside the platform: it sets a context variable and a piece of sender metadata "
            "from its own attributes. No request reaches this addon, so the node is instant and "
            "survives the addon being down."
        ),
        cs=(
            "Běží uvnitř platformy: nastaví kontextovou proměnnou a metadata odesílatele ze svých "
            "atributů. Na addon nedorazí žádný požadavek, takže je uzel okamžitý a funguje, i když "
            "je addon nedostupný."
        ),
    )

    input_attributes = [
        StringAttribute(
            name="tag",
            title=LangString(en="Tag", cs="Štítek"),
            description=LangString(
                en="Value stored in the `conversation_tag` context variable.",
                cs="Hodnota uložená do kontextové proměnné `conversation_tag`.",
            ),
            default_value="vip",
            required=True,
        ),
        StringAttribute(
            name="source",
            title=LangString(en="Source", cs="Zdroj"),
            description=LangString(
                en="Recorded as sender metadata, so you can tell later where the tag came from.",
                cs="Uloží se jako metadata odesílatele, aby bylo poznat, odkud štítek přišel.",
            ),
            default_value="flow",
            required=True,
        ),
    ]

    # What the platform does on this node's behalf. `{tag}` and `{source}` are
    # filled in from the attributes above.
    local_actions = [
        LocalContextAction(name="conversation_tag", value="{tag}"),
        LocalSenderMetadataAction(key="tagged_by", value="{source}"),
    ]

    # A local module must declare **exactly one** output port: with no code
    # running there is nothing to branch on, and `to_manifest()` raises if you
    # declare more. Need a second path? That is a normal (remote) module.
    output_ports = [
        OutputPortStatic(
            name="done",
            title=LangString(en="Done", cs="Hotovo"),
            description=LangString(en="Always taken.", cs="Vždy."),
        ),
    ]
