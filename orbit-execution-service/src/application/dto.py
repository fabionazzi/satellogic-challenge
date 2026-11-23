from dataclasses import dataclass


@dataclass(frozen=True)
class CaptureTaskDTO:
    request_id: str
    target_theta: float


@dataclass(frozen=True)
class TaskAssignmentDTO:
    satellite_id: int
    satellite_name: str
    tasks: list[CaptureTaskDTO]


@dataclass(frozen=True)
class PlanDTO:
    assignments: list[TaskAssignmentDTO]
