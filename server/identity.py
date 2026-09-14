"""Who this addon says it is.

These values become the manifest the platform reads: the name and icon on the
addon card, the `code` it is filed under, the version it caches assets by. See
`docs/reference/manifest.md` for what each one does.

They are **identity, not behaviour** - you set them once when you fork this
template, by editing the defaults below. Every one is also overridable by an
environment variable (`ADDON_CODE`, `ADDON_NAME`, ...), which is what lets a
single image serve more than one environment: a staging deployment can call
itself "Example Addon (staging)" without a rebuild, and CI can inject the
version from a git tag.

Two icon fields exist and the platform prefers `base64_icon` whenever it is
set, falling back to `fa_icon` otherwise - so setting both is fine, and the
bitmap wins. `base64_icon` has to be a complete data URI, because the admin
drops it straight into a CSS `url(...)`.

`code` keeps a default on purpose, so `uv run uvicorn server.main:app` works
on a fresh clone with nothing configured. Leaving it as `example` in a real
deployment is visible rather than silent: the platform enforces a unique
addon code, and every event your modules write shows up in an interaction as
`<module>::<code>`. The startup log prints it too.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AddonIdentity(BaseSettings):
    """Manifest identity, overridable with `ADDON_`-prefixed variables.

    Unrelated `ADDON_*` variables - `ADDON_PROFILE`, `ADDON_URL`,
    `ADDON_SETTINGS_FILE` - belong to other parts of the addon and are ignored
    here.
    """

    model_config = SettingsConfigDict(env_prefix="ADDON_")

    code: str = Field(
        default="example",
        description="Stable identifier in the platform. Change it once, when you fork; never after.",
    )
    name: str = Field(default="Example Addon", description="Display name on the addon card.")
    description: str = Field(
        default="Starter template showing how to build a Daktela AI addon",
        description="One or two sentences, shown on the card.",
    )
    version: str = Field(
        default="1.0.0",
        description="Also appended to the configuration page's bundle URL, so bumping it busts that cache.",
    )
    author: str = Field(default="Your Company", description="Shown on the addon card.")
    fa_icon: str = Field(
        default="puzzle-piece",
        description="Font Awesome icon name, without the `fa-` prefix. Used unless base64_icon is set.",
    )
    base64_icon: str | None = Field(
        default=None,
        description=(
            "Your own 48x48 icon as a full data URI, e.g. `data:image/png;base64,iVBOR...`. "
            "The platform prefers it over fa_icon whenever it is set."
        ),
    )
    color: str = Field(default="#2c6fbb", description="Accent colour; also tints your module nodes.")


def addon_identity() -> AddonIdentity:
    """Read the identity once, at startup."""
    return AddonIdentity()
