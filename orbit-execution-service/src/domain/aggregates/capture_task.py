from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.domain.exceptions import (
    InvalidThetaError,
    NotPersistedError,
    StatusTransitionError,
)
from src.domain.value_objects.capture import (
    CaptureAttemptStatus,
    CaptureResult,
    CaptureTarget,
)


class CaptureTaskStatus(str, Enum):
    """Possible results for a task execution."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


ALLOWED_TRANSITIONS = {
    CaptureTaskStatus.PENDING: {
        CaptureTaskStatus.IN_PROGRESS,
        CaptureTaskStatus.FAILED,
    },
    CaptureTaskStatus.IN_PROGRESS: {
        CaptureTaskStatus.SUCCEEDED,
        CaptureTaskStatus.FAILED,
    },
    CaptureTaskStatus.SUCCEEDED: set(),
    CaptureTaskStatus.FAILED: set(),
}


@dataclass
class CaptureAttempt:
    attempted_at_theta: int
    status: CaptureAttemptStatus
    reason: str | None
    attempted_at: datetime
    attempt_id: int | None = None

    @classmethod
    def from_result(cls, result: CaptureResult) -> "CaptureAttempt":
        return cls(
            attempted_at_theta=result.attempted_at_theta,
            status=result.status,
            reason=result.reason,
            attempted_at=result.attempted_at,
        )


@dataclass
class CaptureTask:
    """Represents an image capture task"""

    plan_id: int
    request_id: str
    satellite_id: int
    satellite_name: str
    target_theta: float
    status: CaptureTaskStatus
    attempts: list[CaptureAttempt]
    task_id: int | None = None

    @classmethod
    def create(
        cls,
        plan_id: int,
        request_id: str,
        satellite_id: int,
        satellite_name: str,
        target_theta: float,
    ) -> "CaptureTask":
        if not 0 <= target_theta < 360:
            raise InvalidThetaError
        return cls(
            plan_id=plan_id,
            request_id=request_id,
            satellite_id=satellite_id,
            satellite_name=satellite_name,
            target_theta=target_theta,
            status=CaptureTaskStatus.PENDING,
            attempts=list(),
        )

    @property
    def target(self) -> CaptureTarget:
        if self.task_id is None:
            raise NotPersistedError(
                "Task must be persisted before being targeted"
            )
        return CaptureTarget(
            task_id=self.task_id, target_theta=self.target_theta
        )

    def _transition_to(self, status: CaptureTaskStatus) -> None:
        if status not in ALLOWED_TRANSITIONS[self.status]:
            raise StatusTransitionError(f"{self.status} -> {status}")
        self.status = status

    def start(self):
        self._transition_to(CaptureTaskStatus.IN_PROGRESS)

    def record_attempt(self, result: CaptureResult) -> CaptureAttempt:
        """Record the capture attempt and finish the task."""
        succeeded = result.status == CaptureAttemptStatus.SUCCEEDED
        self._transition_to(
            CaptureTaskStatus.SUCCEEDED
            if succeeded
            else CaptureTaskStatus.FAILED
        )
        attempt = CaptureAttempt.from_result(result)
        self.attempts.append(attempt)

        return attempt
