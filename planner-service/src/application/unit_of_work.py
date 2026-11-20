from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from src.domain.repositories import (
    CaptureRepository,
    PlannerLockRepository,
    PlanRepository,
)


class UnitOfWork(ABC):
    """Abstract base class for Unit of Work pattern."""

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        pass


class CaptureUOW(UnitOfWork):
    """Unit of Work for capture operations."""

    capture_repository: CaptureRepository
    plan_repository: PlanRepository
    planner_lock: PlannerLockRepository
