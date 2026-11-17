from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.aggregates.plan import Plan


class PlanRepository(ABC):
    """Interface for plan repositories"""

    @abstractmethod
    async def add(self, plan: Plan) -> Plan: ...

    @abstractmethod
    async def get_by_uuid(self, plan_uuid: UUID) -> Plan | None: ...

    @abstractmethod
    async def update(self, plan: Plan): ...
