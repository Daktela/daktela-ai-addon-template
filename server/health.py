"""Health endpoints.

The two probes answer deliberately different questions:

* `/liveness`  - "is this process alive?" It must never touch a dependency.
  A probe that fails when the database blinks makes Kubernetes restart
  perfectly healthy pods, which turns a small outage into a large one.
* `/readiness` - "can this process serve traffic right now?" It asks the
  configured `SettingsStore`, which in the default (json) mode is a no-op.

Both report which profile the process booted with. The two Docker images are
otherwise indistinguishable from outside except by the routes they *lack*, and
that makes for confusing debugging: a basic addon answers 404 on
`/api/example_credentials`, which is also the legitimate "no credentials saved
yet" answer. One curl against `/liveness` settles it.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    """`alive` for liveness; `healthy` / `unhealthy` for readiness."""

    profile: str | None = None
    """`full` or `basic` - see `server/profile.py`."""

    backend: str | None = None
    """Which settings store is live (`json` or `postgres`). Handy while
    learning: it tells you at a glance which mode the addon booted in."""
