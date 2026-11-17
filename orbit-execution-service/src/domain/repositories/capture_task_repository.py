from abc import ABC, abstractmethod

from src.domain.aggregates.capture_task import CaptureTask


class CaptureTaskRepository(ABC):
    """Interface for Capture task repositories"""

    @abstractmethod
    async def add_many(
        self, capture_task: list[CaptureTask]
    ) -> list[CaptureTask]: ...

    @abstractmethod
    async def get(self, capture_task_id: int) -> CaptureTask | None: ...

    @abstractmethod
    async def update(self, capture_task: CaptureTask) -> CaptureTask: ...

    @abstractmethod
    async def list_by_plan(self, plan_id: int) -> list[CaptureTask]: ...
