from datetime import datetime

from pydantic import BaseModel, Field
from src.application.dto import CreateCaptureCommand
from src.domain.aggregates.capture import Capture, CaptureStatus


class CreateCaptureRequest(BaseModel):
    """Request model for creating a new capture."""

    request_id: str
    target_name: str
    target_theta: float = Field(ge=0, lt=360)
    priority: int = Field(ge=0)

    def to_command(self) -> CreateCaptureCommand:
        return CreateCaptureCommand(**self.model_dump())


class CaptureCreateResponse(BaseModel):
    """Response model for capture creation."""

    request_id: str
    status: CaptureStatus

    @classmethod
    def from_domain(cls, capture: Capture) -> "CaptureCreateResponse":
        return cls(
            request_id=capture.request_id,
            status=capture.status,
        )


class ExecutionDetails(BaseModel):
    """Details about the execution of a capture."""

    attempted_at_theta: float | None = Field(ge=0, lt=360)
    completed_at_timestamp: datetime | None = None


class CaptureResponse(BaseModel):
    """Response model for capture information."""

    request_id: str
    status: CaptureStatus
    assigned_satellite: str | None = None
    execution_details: ExecutionDetails | None = None

    @classmethod
    def from_domain(cls, capture: Capture) -> "CaptureResponse":
        last_attempt = capture.last_attempt
        if last_attempt:
            execution_details = ExecutionDetails(
                attempted_at_theta=last_attempt.attempted_at_theta,
                completed_at_timestamp=last_attempt.attempted_at,
            )
            assigned_satellite = last_attempt.assigned_satellite
        else:
            execution_details = None
            assigned_satellite = None
        return cls(
            request_id=capture.request_id,
            status=capture.status,
            assigned_satellite=assigned_satellite,
            execution_details=execution_details,
        )
