"""
Database Session Management
============================

Configures the async SQLAlchemy engine and session factory.
Provides a dependency-injectable session generator for FastAPI.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.settings.config import get_settings

settings = get_settings()

# Create async engine
# SQLite uses aiosqlite; PostgreSQL would use asyncpg
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session.
    
    Usage in endpoints:
        async def endpoint(db: AsyncSession = Depends(get_session)):
            ...
    
    Yields:
        AsyncSession: An active database session.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database.
    
    Creates all tables if they don't exist.
    In production, use Alembic migrations instead.
    """
    from backend.models.base import Base
    # Import all models to register them with Base
    import backend.models  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
