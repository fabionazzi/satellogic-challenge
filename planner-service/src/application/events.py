from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, Self
from uuid import UUID

from src.domain.capture_status import CaptureAttemptStatus

PLAN_PENDING = "plan.pending"
PLAN_IN_PROGRESS = "plan.in_progress"
PLAN_COMPLETED = "plan.completed"
TASK_IN_PROGRESS = "task.in_progress"
TASK_ATTEMPT = "task.attempt"


class ExecutionPlanStatus(str, Enum):
    """Plan status as reported by the orbit execution service."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ExecutionTaskStatus(str, Enum):
    """Task status as reported by the orbit execution service."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class Payload(Protocol):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self: ...


@dataclass(frozen=True)
class PlanPayload:
    """Payload of plan.* events."""

    plan_uuid: UUID
    status: ExecutionPlanStatus

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            plan_uuid=UUID(data["plan_uuid"]),
            status=ExecutionPlanStatus(data["status"]),
        )


@dataclass(frozen=True)
class TaskStartedPayload:
    """Payload of the task.in_progress event."""

    plan_uuid: UUID
    request_id: str
    status: ExecutionTaskStatus

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            plan_uuid=UUID(data["plan_uuid"]),
            request_id=data["request_id"],
            status=ExecutionTaskStatus(data["status"]),
        )


@dataclass(frozen=True)
class TaskAttemptPayload:
    """Capture attempt reported in the task.attempt event."""

    satellite_name: str
    status: CaptureAttemptStatus
    reason: str | None
    attempted_at: datetime
    attempted_at_theta: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            satellite_name=data["satellite_name"],
            status=CaptureAttemptStatus(data["status"]),
            reason=data["reason"],
            attempted_at=datetime.fromisoformat(data["attempted_at"]),
            attempted_at_theta=int(data["attempted_at_theta"]),
        )


@dataclass(frozen=True)
class TaskFinishedPayload:
    """Payload of the task.attempt event."""

    plan_uuid: UUID
    request_id: str
    attempt: TaskAttemptPayload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            plan_uuid=UUID(data["plan_uuid"]),
            request_id=data["request_id"],
            attempt=TaskAttemptPayload.from_dict(data["attempt"]),
        )


@dataclass(frozen=True)
class SimulationEvent[P: Payload]:
    """Event published by the orbit execution service."""

    name: str
    payload: P
    occurred_at: datetime

    @classmethod
    def from_message(
        cls, name: str, body: dict[str, Any], payload_type: type[P]
    ) -> "SimulationEvent[P]":
        data = dict(body)
        occurred_at = datetime.fromisoformat(data.pop("occurred_at"))
        return cls(
            name=name,
            payload=payload_type.from_dict(data),
            occurred_at=occurred_at,
        )


type PlanEvent = SimulationEvent[PlanPayload]
type TaskStartedEvent = SimulationEvent[TaskStartedPayload]
type TaskFinishedEvent = SimulationEvent[TaskFinishedPayload]
