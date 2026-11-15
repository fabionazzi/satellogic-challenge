from dataclasses import dataclass
from datetime import datetime

from src.domain.capture_status import CaptureAttemptStatus


@dataclass
class CaptureAttempt:
    """Capture attempt entity for the orbit execution service."""

    attempt_id: int
    status: CaptureAttemptStatus
    assigned_satellite: str
    attempted_at_theta: float
    attempted_at: datetime
