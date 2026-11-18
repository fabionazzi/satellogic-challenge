from abc import ABC, abstractmethod
from collections.abc import Callable
from types import TracebackType
from typing import Self, TypeAlias

from src.domain.repositories.capture_task_repository import (
    CaptureTaskRepository,
)
from src.domain.repositories.plan_repository import PlanRepository


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


class ExecutionUOW(UnitOfWork):
    """Unit of Work for plan execution operations."""

    plans: PlanRepository
    tasks: CaptureTaskRepository


ExecutionUOWFactory: TypeAlias = Callable[[], ExecutionUOW]
