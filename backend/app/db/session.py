from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db.models import Base

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _migrate_columns(conn):
    """Add missing columns to existing tables (lightweight migration)."""
    migrations = [
        ("users", "email_verified", "BOOLEAN DEFAULT TRUE"),
        ("users", "email_verify_token", "VARCHAR(64)"),
        ("users", "email_verify_sent_at", "TIMESTAMPTZ"),
    ]
    for table, column, col_type in migrations:
        try:
            await conn.execute(
                text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            )
        except Exception:
            pass  # Column already exists


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_columns(conn)


async def get_db():
    async with async_session() as session:
        yield session
