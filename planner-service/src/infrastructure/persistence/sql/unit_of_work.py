from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.unit_of_work import CaptureUOW, UnitOfWork
from src.infrastructure.persistence.sql.repositories import (
    SQLCaptureRepository,
    SQLPlannerLockRepository,
    SQLPlanRepository,
)


class BaseSQLUnitOfWork(UnitOfWork):
    """Base SQL implementation of the Unit of Work pattern."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


class SQLCaptureUnitOfWork(BaseSQLUnitOfWork, CaptureUOW):
    """SQL implementation of the Unit of Work pattern for captures."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        self._sessionmaker = sessionmaker
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        self._session = self._sessionmaker()
        self.capture_repository = SQLCaptureRepository(self._session)
        self.plan_repository = SQLPlanRepository(self._session)
        self.planner_lock = SQLPlannerLockRepository(self._session)
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            await super().__aexit__(exc_type, exc_val, exc_tb)
        finally:
            await self._session.close()
            self._session = None
