from src.domain.aggregates.capture_task import CaptureAttempt, CaptureTask
from src.domain.aggregates.plan import Plan
from src.infrastructure.persistence.sql.models import (
    SQLCaptureTask,
    SQLCaptureTaskAttempt,
    SQLPlan,
)


class PlanMapper:
    """Convert between plan models and plan aggregates."""

    @staticmethod
    def to_domain(model: SQLPlan) -> Plan:
        return Plan(
            plan_id=model.plan_id,
            plan_uuid=model.plan_uuid,
            status=model.status,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )

    @staticmethod
    def to_new_model(plan: Plan) -> SQLPlan:
        return SQLPlan(
            plan_uuid=plan.plan_uuid,
            status=plan.status,
            started_at=plan.started_at,
            completed_at=plan.completed_at,
        )

    @staticmethod
    def apply(plan: Plan, model: SQLPlan) -> None:
        model.status = plan.status
        model.started_at = plan.started_at
        model.completed_at = plan.completed_at


class CaptureAttemptMapper:
    """Convert between attempt models and capture attempts."""

    @staticmethod
    def to_domain(model: SQLCaptureTaskAttempt) -> CaptureAttempt:
        return CaptureAttempt(
            attempt_id=model.attempt_id,
            status=model.status,
            reason=model.reason,
            attempted_at_theta=model.attempted_at_theta,
            attempted_at=model.attempted_at,
        )

    @staticmethod
    def to_new_model(attempt: CaptureAttempt) -> SQLCaptureTaskAttempt:
        return SQLCaptureTaskAttempt(
            status=attempt.status,
            reason=attempt.reason,
            attempted_at_theta=attempt.attempted_at_theta,
            attempted_at=attempt.attempted_at,
        )


class CaptureTaskMapper:
    """Convert between capture task models and capture task aggregates."""

    @staticmethod
    def to_domain(model: SQLCaptureTask) -> CaptureTask:
        return CaptureTask(
            task_id=model.task_id,
            plan_id=model.plan_id,
            request_id=model.request_id,
            satellite_id=model.satellite_id,
            target_theta=model.target_theta,
            status=model.status,
            attempts=[
                CaptureAttemptMapper.to_domain(a) for a in model.attempts
            ],
        )

    @staticmethod
    def to_new_model(task: CaptureTask) -> SQLCaptureTask:
        return SQLCaptureTask(
            plan_id=task.plan_id,
            request_id=task.request_id,
            satellite_id=task.satellite_id,
            target_theta=task.target_theta,
            status=task.status,
            attempts=[
                CaptureAttemptMapper.to_new_model(a) for a in task.attempts
            ],
        )

    @staticmethod
    def apply(task: CaptureTask, model: SQLCaptureTask) -> None:
        model.status = task.status
        for attempt in task.attempts:
            if attempt.attempt_id is None:
                model.attempts.append(
                    CaptureAttemptMapper.to_new_model(attempt)
                )
