from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.settings import Settings


def build_engine(settings: Settings) -> AsyncEngine:
    url = settings.database_url
    return create_async_engine(url, pool_pre_ping=True)


def build_sessionmaker(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
