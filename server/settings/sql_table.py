"""The only database table in this template.

Alembic autogenerates migrations from `metadata` below - see
`migrations/env.py` and `docs/11-persistence.md`.

Dialect-neutrality rule: keep this table portable. No JSONB, no ARRAY, no
`postgresql_*` keyword arguments, no server-side defaults that only Postgres
understands. The test suite creates this table on SQLite so that CI can
exercise `SqlSettingsStore` without running a database server.
"""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel, UniqueConstraint

metadata = SQLModel.metadata


def _now() -> datetime:
    return datetime.now(UTC)


class ExampleCredentialsRow(SQLModel, table=True):
    # pyright flags this because SQLModel types __tablename__ as declared_attr;
    # a plain string is the documented, supported form.
    __tablename__ = "example_credentials"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("customer", "instance_id", name="uq_example_credentials_tenant"),)

    id: int | None = Field(default=None, primary_key=True)

    # The tenant this row belongs to - see `server/settings/models.TenantKey`.
    customer: str = Field(max_length=100, index=True)
    instance_id: int = Field(index=True)

    # Mirrors `ExampleCredentials`. Change both together.
    api_url: str = Field(max_length=200)
    api_token: str = Field(max_length=200)
    display_name: str = Field(max_length=100)

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
