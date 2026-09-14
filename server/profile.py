"""Which surface this addon exposes: `full` or `basic`.

One source tree, two Docker images:

* `docker/Dockerfile` builds the **full** addon - the backend plus the React
  configuration page an operator fills in.
* `docker/Dockerfile.basic` builds the **basic** addon - the backend alone, for
  an addon that only contributes flow-builder modules and has nothing to
  configure. No Node stage, no bundle, a much smaller image.

Both profiles serve every module, integration and dynamic list. The profile
only decides whether the addon has a configuration page.

`ADDON_PROFILE` is read once, in `create_app` (`server/app.py`). It is a plain
function rather than a module-level constant so a test can flip it with
`monkeypatch.setenv` - the same reason `storage_backend()` in `server/di.py` is
a function.
"""

import os
from enum import StrEnum

ADDON_PROFILE_ENV = "ADDON_PROFILE"


class AddonProfile(StrEnum):
    FULL = "full"
    """Backend plus configuration page: `has_setting`, `/api/*`, `/dist`."""

    BASIC = "basic"
    """Backend only - and, importantly, no `GET /instance-configured`."""


def addon_profile() -> AddonProfile:
    """Read `ADDON_PROFILE`. Unset means `full`; anything unknown is an error.

    Deliberately strict. Falling back to `full` on a typo would produce an
    addon that looks fine at boot and then refuses to activate: the full
    profile registers `GET /instance-configured`, that route answers 409 until
    a tenant saves settings, and with no configuration page no tenant ever can.
    The operator would see "activation blocked" in the admin UI, three layers
    and one machine away from the typo. Better to refuse to start.
    """
    raw = os.getenv(ADDON_PROFILE_ENV)
    if not raw:
        return AddonProfile.FULL

    try:
        # Tolerate casing and stray whitespace: this value usually comes from a
        # compose file or a Kubernetes manifest.
        return AddonProfile(raw.strip().lower())
    except ValueError:
        valid = ", ".join(profile.value for profile in AddonProfile)
        message = f"{ADDON_PROFILE_ENV}={raw!r} is not a valid profile. Use one of: {valid}."
        raise ValueError(message) from None
