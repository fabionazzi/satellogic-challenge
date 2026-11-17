from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CaptureAttemptStatus(str, Enum):
    """Possible results for a task execution attempt."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class CaptureTarget:
    task_id: int
    target_theta: float


@dataclass(frozen=True)
class CaptureOutcome:
    status: CaptureAttemptStatus
    reason: str | None = None


@dataclass(frozen=True)
class CaptureResult:
    satellite_id: int
    satellite_name: str
    task_id: int
    attempted_at_theta: int
    status: CaptureAttemptStatus
    reason: str | None
    attempted_at: datetime
