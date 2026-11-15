from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession
from src.application.unit_of_work import CaptureUOW, UnitOfWork
from src.infrastructure.persistence.sql.repositories import (
    SQLCaptureRepository,
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

    async def __aenter__(self) -> Self:
        self.capture_repository = SQLCaptureRepository(self._session)
        return await super().__aenter__()
