from dataclasses import dataclass

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
    CaptureStatus.QUEUED: [CaptureStatus.SCHEDULED, CaptureStatus.REJECTED],
    CaptureStatus.SCHEDULED: [CaptureStatus.IN_PROGRESS],
    CaptureStatus.IN_PROGRESS: [CaptureStatus.SUCCEEDED, CaptureStatus.FAILED],
    CaptureStatus.REJECTED: [],
    CaptureStatus.SUCCEEDED: [],
    CaptureStatus.FAILED: [],
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

    def has_same_request_id(self, other: "Capture") -> bool:
        return self.request_id == other.request_id

    def transition_to(self, status: CaptureStatus) -> None:
        """Transition the capture to a new status."""
        if status not in ALLOWED_TRANSITIONS[self.status]:
            raise StatusTransitionError(
                f"Invalid transition from {self.status} to {status}"
            )
        self.status = status

    def add_attempt(self, attempt: CaptureAttempt) -> None:
        """Add a capture attempt to the capture."""
        if self.status not in [CaptureStatus.SCHEDULED]:
            raise StatusTransitionError(
                f"Cannot add attempt when capture is in {self.status} status"
            )
        attempt_status = attempt.status
        match attempt_status:
            case CaptureAttemptStatus.IN_PROGRESS:
                self.transition_to(CaptureStatus.IN_PROGRESS)
            case CaptureAttemptStatus.SUCCEEDED:
                self.transition_to(CaptureStatus.SUCCEEDED)
            case CaptureAttemptStatus.FAILED:
                self.transition_to(CaptureStatus.FAILED)
            case _:
                raise StatusTransitionError(
                    f"Invalid attempt status {attempt_status}"
                )
        self.attempts.append(attempt)

    def update_attempt(
        self, attempt_id: int, status: CaptureAttemptStatus
    ) -> None:
        """Update the status of a capture attempt."""
        attempt = next(
            (a for a in self.attempts if a.attempt_id == attempt_id), None
        )
        if not attempt:
            raise ValueError(f"Attempt with id {attempt_id} not found")
        attempt.status = status
        self.add_attempt(attempt)

    @property
    def last_attempt(self) -> CaptureAttempt | None:
        """Return the last capture attempt, if any."""
        if not self.attempts:
            return None
        self.attempts.sort(key=lambda a: a.attempted_at)
        return self.attempts[-1]
