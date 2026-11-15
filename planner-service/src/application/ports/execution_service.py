from abc import ABC, abstractmethod
from enum import Enum


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionPlan:
    pass


class ExecutionService(ABC):
    """Interface for an execution service that can dispatch execution
    plans."""

    @abstractmethod
    async def dispatch(self, plan: ExecutionPlan) -> None:
        """Dispatch the execution plan to the appropriate execution
        service."""
        pass

    @abstractmethod
    async def get_status(self) -> ExecutionStatus:
        """Get the status of the execution plan."""
        pass
