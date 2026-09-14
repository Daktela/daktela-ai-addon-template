"""Level-2 settings store: one row per tenant in a real database.

Enabled by setting the `db_*` environment variables - nothing here runs until
you do. See `docs/11-persistence.md` for the four commands that turn it on.
"""

from datetime import UTC, datetime

from cw_database.session_factory import SessionFactory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.settings.models import ExampleCredentials, TenantKey
from server.settings.sql_table import ExampleCredentialsRow


class SqlSettingsStore:
    name = "postgres"

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get(self, tenant: TenantKey) -> ExampleCredentials | None:
        async with self._session_factory() as session:
            row = await self._find(session, tenant)
            return None if row is None else self._to_model(row)

    async def set(self, tenant: TenantKey, credentials: ExampleCredentials) -> ExampleCredentials:
        # Deliberately select-then-insert-or-update rather than an
        # `INSERT ... ON CONFLICT`: the plain form works on every SQL dialect,
        # which is what lets the test suite run this class on SQLite.
        async with self._session_factory() as session:
            row = await self._find(session, tenant)

            if row is None:
                session.add(
                    ExampleCredentialsRow(
                        customer=tenant.customer,
                        instance_id=tenant.instance_id,
                        **credentials.model_dump(),
                    )
                )
            else:
                for field, value in credentials.model_dump().items():
                    setattr(row, field, value)
                row.updated_at = datetime.now(UTC)
                session.add(row)

            await session.commit()

        return credentials

    async def delete(self, tenant: TenantKey) -> None:
        async with self._session_factory() as session:
            row = await self._find(session, tenant)
            if row is not None:
                await session.delete(row)
                await session.commit()

    async def health(self) -> None:
        async with self._session_factory() as session:
            await session.execute(text("SELECT 1"))

    @staticmethod
    async def _find(session: AsyncSession, tenant: TenantKey) -> ExampleCredentialsRow | None:
        statement = select(ExampleCredentialsRow).where(
            ExampleCredentialsRow.customer == tenant.customer,
            ExampleCredentialsRow.instance_id == tenant.instance_id,
        )
        result = await session.execute(statement)
        return result.scalars().first()

    @staticmethod
    def _to_model(row: ExampleCredentialsRow) -> ExampleCredentials:
        return ExampleCredentials(
            api_url=row.api_url,
            api_token=row.api_token,
            display_name=row.display_name,
        )
