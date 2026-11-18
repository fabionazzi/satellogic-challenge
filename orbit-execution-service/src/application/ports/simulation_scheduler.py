from abc import ABC, abstractmethod
from uuid import UUID


class SimulationScheduler(ABC):
    """Port for simulation schedulers"""

    @abstractmethod
    async def schedule(self, plan_uuid: UUID) -> None: ...
