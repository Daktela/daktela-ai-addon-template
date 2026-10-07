"""The two rich form controls: a chips list and a WYSIWYG editor.

Demonstrates : `StringListAttribute` (a chips input, one chip per value) and
               `HtmlAttribute` (a multi-line field whose pencil icon opens the
               builder's WYSIWYG editor; the value arrives as an HTML string).
Documented in: docs/reference/attributes.md
Change first : what `execute()` does with the recipients and the body.

The form this renders is the same pair of controls the builder's native
"Send email" node uses for its recipients and its message body. This module
does not send anything - it only shows what the two attributes deliver.
"""

from typing import override

from cw_addons.modules.executor import ModuleExecutor
from cw_addons.modules.models import (
    HtmlAttribute,
    LangString,
    ModuleResponses,
    OutputContext,
    OutputPortStatic,
    StringAttribute,
    StringListAttribute,
)
from cw_addons.modules.module import Module
from pydantic import BaseModel


class EmailDraftAttributes(BaseModel):
    recipients: list[str]
    subject: str | None = None
    body: str


class EmailDraftModule(Module[EmailDraftAttributes]):
    attributes: EmailDraftAttributes

    name = "email_draft"
    version = "v1"
    public = True

    icon = "✉️"
    category = LangString(en="Examples", cs="Příklady")
    title = LangString(en="Email Draft", cs="Koncept emailu")
    short_description = LangString(
        en="Shows the chips list and the WYSIWYG editor controls.",
        cs="Ukazuje ovládací prvky chips seznamu a WYSIWYG editoru.",
    )
    description = LangString(
        en=(
            "Collects recipients as chips and a body in the WYSIWYG editor, then exposes both "
            "as context variables. Nothing is sent - it only demonstrates the two controls."
        ),
        cs=(
            "Sbírá příjemce jako chips a tělo ve WYSIWYG editoru a obojí vystaví jako kontextové "
            "proměnné. Nic neodesílá - jen ukazuje oba ovládací prvky."
        ),
    )

    input_attributes = [
        StringListAttribute(
            name="recipients",
            title=LangString(en="Recipients", cs="Příjemci"),
            description=LangString(
                en="Type an address and press Enter to add it as a chip.",
                cs="Napište adresu a stiskněte Enter, přidá se jako chip.",
            ),
            required=True,
        ),
        StringAttribute(
            name="subject",
            title=LangString(en="Subject", cs="Předmět"),
            description=LangString(en="Plain single-line text.", cs="Jednořádkový text."),
        ),
        HtmlAttribute(
            name="body",
            title=LangString(en="Body", cs="Tělo"),
            description=LangString(
                en="Click the pencil to edit in the WYSIWYG editor. Arrives as HTML.",
                cs="Klikněte na tužku pro úpravu ve WYSIWYG editoru. Přijde jako HTML.",
            ),
            default_value="<p>Hello,</p>",
            required=True,
        ),
    ]

    output_contexts = [
        OutputContext(
            name="email_recipients",
            title=LangString(en="Email recipients", cs="Příjemci emailu"),
            description=LangString(en="The recipients, comma-separated.", cs="Příjemci oddělení čárkou."),
        ),
        OutputContext(
            name="email_body",
            title=LangString(en="Email body", cs="Tělo emailu"),
            description=LangString(en="The body as HTML.", cs="Tělo jako HTML."),
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
        executor = ModuleExecutor(
            discussion=self.discussion,
            attributes=self.attributes,
            tenant=self.tenant,
            module_name=self.name,
        )
        executor.add_context("email_recipients", ", ".join(self.attributes.recipients))
        executor.add_context("email_body", self.attributes.body)
        executor.add_message(f"Draft for {len(self.attributes.recipients)} recipient(s) prepared.")
        executor.add_output_port("done")
        return executor.get_response()
