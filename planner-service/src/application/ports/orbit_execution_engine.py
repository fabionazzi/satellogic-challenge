from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.value_objects.satellite import Satellite, SatelliteAssignment


class OrbitExecutionService(ABC):
    """Interface for an execution service that can dispatch execution
    plans."""

    @abstractmethod
    async def dispatch(
        self, plan_uuid: UUID, plan: list[SatelliteAssignment]
    ) -> None:
        """Dispatch the execution plan to the appropriate execution
        service."""
        pass

    @abstractmethod
    async def get_constellation(self) -> list[Satellite]:
        """Get constellation information."""
