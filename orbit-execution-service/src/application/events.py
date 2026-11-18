from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.domain.aggregates.capture_task import CaptureAttempt, CaptureTask
from src.domain.aggregates.plan import Plan


@dataclass(frozen=True)
class SimulationEvent:
    name: str
    payload: dict[str, Any]
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventFactory:
    """Responsible for creating events"""

    @staticmethod
    def create_plan_event(plan: Plan) -> SimulationEvent:
        return SimulationEvent(
            name=f"plan.{plan.status.value.lower()}",
            payload={
                "plan_id": str(plan.plan_uuid),
                "status": plan.status.value,
            },
        )

    @staticmethod
    def create_task_event(
        plan: Plan, task: CaptureTask, attempt: CaptureAttempt
    ) -> SimulationEvent:
        return SimulationEvent(
            name=f"task.{task.status.value.lower()}",
            payload={
                "plan_id": str(plan.plan_uuid),
                "request_id": task.request_id,
                "satellite_id": task.satellite_id,
                "status": task.status.value,
                "attempt": {
                    "status": attempt.status.value,
                    "reason": attempt.reason,
                    "attempted_at": attempt.attempted_at.isoformat(),
                    "attempted_at_theta": attempt.attempted_at_theta,
                },
            },
        )

    @staticmethod
    def create_task_started_event(
        plan: Plan, task: CaptureTask
    ) -> SimulationEvent:
        return SimulationEvent(
            name=f"task.{task.status.value.lower()}",
            payload={
                "plan_id": str(plan.plan_uuid),
                "request_id": task.request_id,
                "satellite_id": task.satellite_id,
                "status": task.status.value,
            },
        )
