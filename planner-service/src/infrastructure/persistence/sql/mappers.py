from src.domain.aggregates.capture import Capture
from src.domain.aggregates.plan import Plan
from src.domain.entities.capture_attempt import CaptureAttempt
from src.infrastructure.persistence.sql.models import (
    SQLCapture,
    SQLCaptureAttempt,
    SQLPlan,
    SQLPlanCapture,
)


class CaptureAttemptMapper:
    """Convert between attempt models and capture attempts."""

    @staticmethod
    def to_domain(model: SQLCaptureAttempt) -> CaptureAttempt:
        return CaptureAttempt(
            attempt_id=model.attempt_id,
            status=model.status,
            assigned_satellite=model.assigned_satellite,
            attempted_at_theta=model.attempted_at_theta,
            attempted_at=model.attempted_at,
        )

    @staticmethod
    def to_new_model(attempt: CaptureAttempt) -> SQLCaptureAttempt:
        return SQLCaptureAttempt(
            status=attempt.status,
            assigned_satellite=attempt.assigned_satellite,
            attempted_at_theta=attempt.attempted_at_theta,
            attempted_at=attempt.attempted_at,
        )


class CaptureMapper:
    """Convert between capture models and capture aggregates."""

    @staticmethod
    def to_domain(model: SQLCapture) -> Capture:
        return Capture(
            capture_id=model.capture_id,
            request_id=model.request_id,
            target_name=model.target_name,
            target_theta=model.target_theta,
            priority=model.priority,
            status=model.status,
            attempts=[
                CaptureAttemptMapper.to_domain(a) for a in model.attempts
            ],
        )

    @staticmethod
    def to_new_model(capture: Capture) -> SQLCapture:
        return SQLCapture(
            request_id=capture.request_id,
            target_name=capture.target_name,
            target_theta=capture.target_theta,
            priority=capture.priority,
            status=capture.status,
            attempts=[
                CaptureAttemptMapper.to_new_model(a) for a in capture.attempts
            ],
        )

    @staticmethod
    def apply(capture: Capture, model: SQLCapture) -> None:
        model.status = capture.status
        existing = {a.attempt_id: a for a in model.attempts}
        for attempt in capture.attempts:
            if attempt.attempt_id is None:
                model.attempts.append(
                    CaptureAttemptMapper.to_new_model(attempt)
                )
            elif attempt.attempt_id in existing:
                existing[attempt.attempt_id].status = attempt.status


class PlanMapper:
    """Convert between plan models and plan aggregates."""

    @staticmethod
    def to_domain(model: SQLPlan) -> Plan:
        return Plan(
            plan_id=model.plan_id,
            plan_uuid=model.plan_uuid,
            capture_ids=[link.capture_id for link in model.capture_links],
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
            capture_links=[
                SQLPlanCapture(capture_id=capture_id)
                for capture_id in plan.capture_ids
            ],
        )

    @staticmethod
    def apply(plan: Plan, model: SQLPlan) -> None:
        model.status = plan.status
        model.started_at = plan.started_at
        model.completed_at = plan.completed_at
