"""Database engine and session management."""

from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from phoneangel.config import settings

async_engine: AsyncEngine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

async_session_factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables on startup."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Dependency-injectable async session."""
    async with async_session_factory() as session:
        yield session
