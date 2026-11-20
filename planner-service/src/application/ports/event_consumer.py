from abc import ABC, abstractmethod

from src.application.events import SimulationEvent


class SimulationEventConsumer(ABC):
    """Interface for event consumers."""

    @abstractmethod
    async def read(self) -> SimulationEvent:
        """Wait for the next event."""

    @abstractmethod
    async def ack(self) -> None:
        """Confirm the last read event was handled."""

    @abstractmethod
    async def reject(self, requeue: bool) -> None:
        """Reject the last read event, optionally requeueing it."""

    @abstractmethod
    async def close(self) -> None:
        """Release the underlying resources."""
