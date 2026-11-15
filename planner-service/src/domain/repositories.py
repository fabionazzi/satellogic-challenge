from abc import ABC, abstractmethod

from src.domain.aggregates.capture import Capture


class CaptureRepository(ABC):
    """Abstract base class for capture repository."""

    @abstractmethod
    async def save(self, capture: Capture) -> None:
        """Add a new capture to the repository."""
        pass

    @abstractmethod
    async def get_by_id(self, capture_id: int) -> Capture:
        """Retrieve a capture by its ID."""
        pass

    @abstractmethod
    async def get_by_request_id(self, request_id: str) -> Capture:
        """Retrieve a capture by its request ID."""
        pass
