from sqlalchemy.ext.asyncio import AsyncSession
from src.application.unit_of_work import UnitOfWork


class BaseSQLUnitOfWork(UnitOfWork):
    """Base SQL implementation of the Unit of Work pattern."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
