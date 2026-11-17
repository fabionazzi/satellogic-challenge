from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID

from src.domain.exceptions import StatusTransitionError


class PlanStatus(str, Enum):
    """Possible results for a plan lifecycle."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


ALLOWED_TRANSITIONS = {
    PlanStatus.PENDING: {PlanStatus.IN_PROGRESS},
    PlanStatus.IN_PROGRESS: {PlanStatus.COMPLETED},
    PlanStatus.COMPLETED: set(),
}


@dataclass
class Plan:
    """Represents a plan"""

    plan_uuid: UUID
    status: PlanStatus
    started_at: datetime | None
    completed_at: datetime | None
    plan_id: int | None = None

    @classmethod
    def create(
        cls,
        plan_uuid: UUID,
    ) -> "Plan":
        return cls(plan_uuid=plan_uuid, status=PlanStatus.PENDING)

    def _transition_to(self, status: PlanStatus) -> None:
        if status not in ALLOWED_TRANSITIONS[self.status]:
            raise StatusTransitionError(f"{self.status} -> {status}")
        self.status = status

    def start(self):
        self._transition_to(PlanStatus.IN_PROGRESS)
        self.started_at = datetime.now(UTC)

    def complete(self):
        self._transition_to(PlanStatus.COMPLETED)
        self.completed_at = datetime.now(UTC)
