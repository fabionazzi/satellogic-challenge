from dataclasses import dataclass
from datetime import datetime

from src.domain.capture_status import CaptureStatus
from src.domain.entities.capture_attempt import (
    CaptureAttempt,
    CaptureAttemptStatus,
)
from src.domain.exceptions import (
    InvalidPriorityError,
    InvalidThetaError,
    StatusTransitionError,
)

ALLOWED_TRANSITIONS = {
    CaptureStatus.QUEUED: {CaptureStatus.SCHEDULED, CaptureStatus.REJECTED},
    CaptureStatus.SCHEDULED: {
        CaptureStatus.IN_PROGRESS,
        CaptureStatus.QUEUED,
        CaptureStatus.FAILED,
    },
    CaptureStatus.IN_PROGRESS: {CaptureStatus.SUCCEEDED, CaptureStatus.FAILED},
    CaptureStatus.REJECTED: set(),
    CaptureStatus.SUCCEEDED: set(),
    CaptureStatus.FAILED: set(),
}

ATTEMPT_TO_CAPTURE_STATUS = {
    CaptureAttemptStatus.SUCCEEDED: CaptureStatus.SUCCEEDED,
    CaptureAttemptStatus.FAILED: CaptureStatus.FAILED,
}


@dataclass
class Capture:
    request_id: str
    target_name: str
    target_theta: float
    priority: int
    status: CaptureStatus
    attempts: list[CaptureAttempt]
    capture_id: int | None = None

    @classmethod
    def create(
        cls,
        request_id: str,
        target_name: str,
        target_theta: float,
        priority: int,
    ) -> "Capture":
        """Factory for new captures."""
        if not 0 <= target_theta < 360:
            raise InvalidThetaError(target_theta)
        if priority < 0:
            raise InvalidPriorityError(priority)
        return cls(
            capture_id=None,
            request_id=request_id,
            target_name=target_name,
            target_theta=target_theta,
            priority=priority,
            status=CaptureStatus.QUEUED,
            attempts=[],
        )

    def is_equal(self, other: "Capture") -> bool:
        return (
            self.request_id == other.request_id
            and self.target_name == other.target_name
            and self.target_theta == other.target_theta
            and self.priority == other.priority
        )

    def transition_to(self, status: CaptureStatus) -> None:
        """Transition the capture to a new status."""
        if status not in ALLOWED_TRANSITIONS[self.status]:
            raise StatusTransitionError(
                f"Invalid transition from {self.status} to {status}"
            )
        self.status = status

    def requeue(self) -> None:
        """Return a scheduled capture to the queue"""
        self.transition_to(CaptureStatus.QUEUED)

    def record_attempt(
        self,
        status: CaptureAttemptStatus,
        satellite: str,
        theta: float,
        at: datetime,
        reason: str | None = None,
    ) -> None:
        """Register new attempt."""
        self.transition_to(ATTEMPT_TO_CAPTURE_STATUS[status])
        self.attempts.append(
            CaptureAttempt(
                status=status,
                assigned_satellite=satellite,
                attempted_at_theta=theta,
                attempted_at=at,
                reason=reason,
            )
        )

    def start(self):
        """Change status to IN_PROGRESS"""
        self.transition_to(CaptureStatus.IN_PROGRESS)

    def fail(self):
        """Mark capture as failed"""
        self.transition_to(CaptureStatus.FAILED)

    def not_completed(self) -> bool:
        return self.status in {
            CaptureStatus.SCHEDULED,
            CaptureStatus.IN_PROGRESS,
        }

    @property
    def last_attempt(self) -> CaptureAttempt | None:
        """Return the last capture attempt, if any."""
        if not self.attempts:
            return None
        self.attempts.sort(key=lambda a: a.attempted_at)
        return self.attempts[-1]
