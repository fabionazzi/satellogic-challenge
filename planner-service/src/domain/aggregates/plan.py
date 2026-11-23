from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from src.domain.exceptions import StatusTransitionError


class PlanStatus(str, Enum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    DISPATCH_FAILED = "DISPATCH_FAILED"
    COMPLETED = "COMPLETED"


ALLOWED_TRANSITIONS = {
    PlanStatus.PENDING: {
        PlanStatus.DISPATCHED,
        PlanStatus.DISPATCH_FAILED,
        PlanStatus.RUNNING,
    },
    PlanStatus.DISPATCHED: {PlanStatus.RUNNING},
    PlanStatus.RUNNING: {PlanStatus.COMPLETED},
    PlanStatus.DISPATCH_FAILED: set(),
    PlanStatus.COMPLETED: set(),
}


@dataclass
class Plan:
    """Represents a plan"""

    plan_uuid: UUID
    capture_ids: list[int]
    status: PlanStatus = PlanStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    plan_id: int | None = None

    @classmethod
    def create(cls, capture_ids: list[int]) -> "Plan":
        return cls(plan_uuid=uuid4(), capture_ids=list(capture_ids))

    def _transition_to(self, to: PlanStatus):
        if to not in ALLOWED_TRANSITIONS[self.status]:
            raise StatusTransitionError(
                f"Invalid transition from {self.status} -> {to}"
            )
        self.status = to

    def start(self, at: datetime):
        self._transition_to(PlanStatus.RUNNING)
        self.started_at = at

    def dispatch(self):
        self._transition_to(PlanStatus.DISPATCHED)

    def dispatch_failed(self):
        self._transition_to(PlanStatus.DISPATCH_FAILED)

    def complete(self, at: datetime):
        self._transition_to(PlanStatus.COMPLETED)
        self.completed_at = at
