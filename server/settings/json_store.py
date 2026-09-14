"""Default settings store: in memory, optionally mirrored to a JSON file.

This is what makes `uv run uvicorn server.main:app --reload` work with no
Docker and no database. It is genuinely usable for local development and for
single-replica deployments that can afford to lose settings on restart.

It is *not* shared between replicas and it is not durable unless you point
`ADDON_SETTINGS_FILE` at a path. That is exactly the problem `SqlSettingsStore`
solves - see `docs/11-persistence.md`.
"""

import asyncio
import json
from pathlib import Path

from server.settings.models import ExampleCredentials, TenantKey


class JsonSettingsStore:
    name = "json"

    def __init__(self, path: Path | None = None) -> None:
        """`path` comes from `ADDON_SETTINGS_FILE`; when unset the store is
        purely in-memory and forgets everything on restart."""
        self._path = path
        self._lock = asyncio.Lock()
        self._rows: dict[str, ExampleCredentials] = self._load()

    async def get(self, tenant: TenantKey) -> ExampleCredentials | None:
        async with self._lock:
            return self._rows.get(tenant.storage_key)

    async def set(self, tenant: TenantKey, credentials: ExampleCredentials) -> ExampleCredentials:
        async with self._lock:
            self._write({**self._rows, tenant.storage_key: credentials})
        return credentials

    async def delete(self, tenant: TenantKey) -> None:
        async with self._lock:
            remaining = {key: value for key, value in self._rows.items() if key != tenant.storage_key}
            self._write(remaining)

    async def health(self) -> None:
        """Nothing to check - an in-process dict cannot be down."""
        return

    def _load(self) -> dict[str, ExampleCredentials]:
        if self._path is None or not self._path.is_file():
            return {}

        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return {key: ExampleCredentials.model_validate(value) for key, value in raw.items()}

    def _write(self, rows: dict[str, ExampleCredentials]) -> None:
        """Persist first, then accept into memory.

        If the file cannot be written - a read-only volume, a permissions
        problem - this raises and the in-memory state is left untouched, so
        memory and disk can never disagree about what was saved.
        """
        self._flush(rows)
        self._rows = rows

    def _flush(self, rows: dict[str, ExampleCredentials]) -> None:
        if self._path is None:
            return

        payload = {key: value.model_dump(mode="json") for key, value in rows.items()}
        # Write to a sibling file first, then rename: a crash mid-write cannot
        # leave a half-written settings file behind.
        temporary = self._path.with_suffix(".tmp")
        temporary.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self._path)
