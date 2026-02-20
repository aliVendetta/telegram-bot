"""Async SQLAlchemy database engine and session management."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def _build_engine_args(url: str) -> dict:
    """Build engine kwargs based on database backend."""
    args: dict = {"echo": False}
    if url.startswith("sqlite"):
        # SQLite doesn't support pool_size / max_overflow
        args["connect_args"] = {"check_same_thread": False}
    else:
        args["pool_size"] = 5
        args["max_overflow"] = 10
        args["pool_pre_ping"] = True
    return args


settings = get_settings()

engine = create_async_engine(settings.database_url, **_build_engine_args(settings.database_url))

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session (for dependency injection).

    Usage:
        async with get_session() as session:
            ...
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
    """Create database tables if they don't exist (dev convenience).

    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialised")
