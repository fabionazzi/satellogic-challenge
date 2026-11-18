from abc import ABC, abstractmethod

from src.application.events import SimulationEvent


class EventPublisher(ABC):
    """Port for simulation event publishers"""

    @abstractmethod
    async def publish(self, event: SimulationEvent) -> None:
        """Publish an event."""
        pass
