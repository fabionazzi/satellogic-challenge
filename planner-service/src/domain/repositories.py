from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.aggregates.capture import Capture, CaptureStatus
from src.domain.aggregates.plan import Plan


class CaptureRepository(ABC):
    """Abstract base class for capture repository."""

    @abstractmethod
    async def add(self, capture: Capture) -> Capture:
        """Add a new capture to the repository"""
        pass

    @abstractmethod
    async def update(self, capture: Capture) -> Capture:
        """Persist changes to an existing capture."""
        pass

    @abstractmethod
    async def get_by_id(self, capture_id: int) -> Capture | None:
        """Retrieve a capture by its ID."""
        pass

    @abstractmethod
    async def get_by_request_id(self, request_id: str) -> Capture | None:
        """Retrieve a capture by its request ID."""
        pass

    @abstractmethod
    async def get_by_plan_uuid(self, plan_uuid: UUID) -> list[Capture]:
        """Retrieve the captures assigned to a plan uuid."""
        pass

    @abstractmethod
    async def all_by_status(self, status: CaptureStatus) -> dict[str, Capture]:
        """Retrieve all captures with a specific status"""
        pass

    @abstractmethod
    async def update_many(self, captures: list[Capture]) -> list[Capture]:
        """Persist changes to many existing captures."""
        pass


class PlanRepository(ABC):
    """Interface for plan repositories."""

    @abstractmethod
    async def add(self, plan: Plan) -> Plan: ...

    @abstractmethod
    async def get_by_uuid(self, plan_uuid: UUID) -> Plan | None: ...

    @abstractmethod
    async def update(self, plan: Plan) -> Plan: ...


class PlannerLockRepository(ABC):
    """Interface for the global planner lock held while a plan is active."""

    @abstractmethod
    async def acquire(self) -> None:
        """Lock exclusively for this transaction; raise if a plan is active."""

    @abstractmethod
    async def bind(self, plan_id: int) -> None:
        """Mark the given plan as the active plan holding the lock."""

    @abstractmethod
    async def reject_if_plan_active(self) -> None:
        """Lock in shared mode for this transaction; raise if plan active."""

    @abstractmethod
    async def release(self, plan_id: int) -> None:
        """Release the lock if it is held by the given plan."""
