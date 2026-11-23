from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession
from src.application.unit_of_work import ExecutionUOW, UnitOfWork
from src.infrastructure.persistence.sql.repositories import (
    SQLCaptureTaskRepository,
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


class SQLExecutionUnitOfWork(BaseSQLUnitOfWork, ExecutionUOW):
    """SQL Unit of Work for plan execution."""

    async def __aenter__(self) -> Self:
        self.plans = SQLPlanRepository(self._session)
        self.tasks = SQLCaptureTaskRepository(self._session)
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
