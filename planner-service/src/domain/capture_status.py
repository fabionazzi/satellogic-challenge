from enum import Enum


class CaptureStatus(str, Enum):
    """Capture status."""

    QUEUED = "QUEUED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    REJECTED = "REJECTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class CaptureAttemptStatus(str, Enum):
    """Capture attempt status for the orbit execution service."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
