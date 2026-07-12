from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def _migrate_sqlite_schema(sync_conn) -> None:
    """Add columns missing from older SQLite DBs (create_all does not ALTER)."""
    from sqlalchemy import inspect, text

    inspector = inspect(sync_conn)
    tables = set(inspector.get_table_names())

    def cols(table: str) -> set[str]:
        if table not in tables:
            return set()
        return {c["name"] for c in inspector.get_columns(table)}

    alters: list[tuple[str, str, str]] = [
        ("laundry_hosts", "welcome_basket_credits", "INTEGER NOT NULL DEFAULT 0"),
        ("laundry_hosts", "prepaid_balance_cents", "INTEGER NOT NULL DEFAULT 0"),
        ("laundry_hosts", "locked_basket_spec", "TEXT"),
        ("laundry_hosts", "program", "VARCHAR(64) NOT NULL DEFAULT 'laundry'"),
        ("treasury_ledger", "payment_category", "VARCHAR(32)"),
        ("ground_force_missions", "lead_id", "INTEGER"),
        ("ground_force_missions", "host_payment_ledger_id", "INTEGER"),
    ]
    for table, column, typedef in alters:
        if table in tables and column not in cols(table):
            sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {typedef}"))


async def init_db() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.database_url.startswith("sqlite"):
            await conn.run_sync(_migrate_sqlite_schema)
