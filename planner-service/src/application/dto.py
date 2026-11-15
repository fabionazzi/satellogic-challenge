from dataclasses import dataclass


@dataclass(frozen=True)
class CreateCaptureCommand:
    """Command to create a new capture."""

    request_id: str
    target_name: str
    target_theta: float
    priority: int
