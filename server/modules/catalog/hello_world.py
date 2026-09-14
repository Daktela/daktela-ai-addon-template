"""The smallest possible module. Start here.

Demonstrates : the manifest fields every module needs, one input attribute,
               and returning a single chat message.
Documented in: docs/04-your-first-module.md
Change first : `name`, `title` and the `execute()` body.

Every `.py` file in this directory is discovered automatically at startup and
must contain exactly one `Module` subclass. There is no registry to edit and
no import to add - dropping a file in here is what "adding a module" means.
"""

from typing import override

from cw_addons.modules.models import (
    ContextAction,
    LangString,
    MessageAction,
    ModuleResponses,
    OutputContext,
    OutputPortAction,
    OutputPortStatic,
    ResultContext,
    StringAttribute,
)
from cw_addons.modules.module import Module
from pydantic import BaseModel


class HelloWorldAttributes(BaseModel):
    """Typed view of what the flow designer filled in.

    The field names must match the `name` of the entries in
    `input_attributes` below. This class exists purely so that
    `self.attributes.greeting` is type-checked - the schema the platform
    actually validates against is generated from `input_attributes`.
    """

    greeting: str


class HelloWorldModule(Module[HelloWorldAttributes]):
    attributes: HelloWorldAttributes

    # --- identity -----------------------------------------------------
    name = "hello_world"
    """Unique within this addon. Bot-platform stores it, so renaming a
    published module orphans every flow that used it."""

    version = "v1"
    """Bump this whenever you change anything else on the class. The platform
    updates a module it already knows only when its version changes - otherwise
    the builder keeps showing the old attributes and ports, with no warning."""

    public = True
    """`public = True` is what makes this module appear in the builder's module
    selection. Set it to False for modules you only call internally."""

    # --- how it looks in the builder ----------------------------------
    icon = "👋"
    category = LangString(en="Examples", cs="Příklady")
    """The group this module appears under in the builder's module selection."""
    title = LangString(en="Hello World", cs="Hello World")
    short_description = LangString(
        en="Sends a greeting back to the customer.",
        cs="Pošle zákazníkovi pozdrav.",
    )
    description = LangString(
        en="The simplest possible module: it takes one text attribute and sends it as a bot message.",
        cs="Nejjednodušší možný modul: vezme jeden textový atribut a pošle ho jako zprávu bota.",
    )

    # --- the form the flow designer fills in --------------------------
    input_attributes = [
        StringAttribute(
            name="greeting",
            title=LangString(en="Greeting", cs="Pozdrav"),
            description=LangString(
                en="Text sent to the customer.",
                cs="Text, který se pošle zákazníkovi.",
            ),
            default_value="Hello from your first addon module!",
            required=True,
        ),
    ]

    # --- what the module hands back to the flow -----------------------
    output_contexts = [
        OutputContext(
            name="greeting_sent",
            title=LangString(en="Greeting sent", cs="Odeslaný pozdrav"),
            description=LangString(
                en="The text that was sent, available to later nodes as a context variable.",
                cs="Odeslaný text, dostupný dalším uzlům jako kontextová proměnná.",
            ),
        ),
    ]

    output_ports = [
        OutputPortStatic(
            name="done",
            title=LangString(en="Done", cs="Hotovo"),
            description=LangString(en="Always taken.", cs="Vždy."),
        ),
    ]

    @override
    async def execute(self) -> ModuleResponses:
        """Called by the platform on `POST /module/v1/execute/hello_world`.

        Returning `ModuleResponses` directly is fine for something this small.
        Once you need more than a couple of actions, use `ModuleExecutor` -
        see `interaction_event.py`.
        """
        return ModuleResponses(
            actions=[
                MessageAction(text=self.attributes.greeting),
                ContextAction(contexts=[ResultContext(name="greeting_sent", value=self.attributes.greeting)]),
                OutputPortAction(name="done"),
            ],
            sequence=self.discussion.sequence + 1,
        )
