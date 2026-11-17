from abc import ABC, abstractmethod


class EventPublisher(ABC):
    """Abstract class for event publishers"""

    @abstractmethod
    async def publish(self, message) -> None: ...
