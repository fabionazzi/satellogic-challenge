from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from src.domain.aggregates.capture_task import (
    CaptureTaskStatus,
)
from src.domain.aggregates.plan import PlanStatus
from src.domain.value_objects.capture import CaptureAttemptStatus

ACTIVE_PLAN_STATUSES = (PlanStatus.PENDING, PlanStatus.IN_PROGRESS)
ACTIVE_SLOT_COLUMN = "active_slot"


class SQLBase(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin class for timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SQLPlan(SQLBase, TimestampMixin):
    """SQLAlchemy model for plans."""

    __tablename__ = "plan"
    __table_args__ = (
        UniqueConstraint(ACTIVE_SLOT_COLUMN, name="uq_plan_active_slot"),
    )

    plan_id: Mapped[int] = mapped_column(primary_key=True)
    plan_uuid: Mapped[UUID] = mapped_column(unique=True, nullable=False)
    status: Mapped[PlanStatus] = mapped_column(
        SAEnum(
            PlanStatus,
            name="plan_status",
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
        ),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    active_slot: Mapped[int | None] = mapped_column(
        Computed(
            "CASE WHEN status IN ("
            + ", ".join(f"'{s.value}'" for s in ACTIVE_PLAN_STATUSES)
            + ") THEN 1 ELSE NULL END",
            persisted=True,
        )
    )

    tasks: Mapped[list["SQLCaptureTask"]] = relationship(
        back_populates="plan",
        lazy="raise",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SQLCaptureTask.task_id",
    )


class SQLCaptureTask(SQLBase):
    """SQLAlchemy model for capture tasks."""

    __tablename__ = "capture_task"
    __table_args__ = (
        CheckConstraint(
            "target_theta >= 0 AND target_theta < 360",
            name="check_target_theta_range",
        ),
    )

    task_id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plan.plan_id", ondelete="CASCADE"), nullable=False
    )
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    satellite_id: Mapped[int] = mapped_column(nullable=False)
    satellite_name: Mapped[str] = mapped_column(String(64), nullable=False)
    target_theta: Mapped[float] = mapped_column(nullable=False)
    status: Mapped[CaptureTaskStatus] = mapped_column(
        SAEnum(
            CaptureTaskStatus,
            name="capture_task_status",
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
        ),
        nullable=False,
    )

    plan: Mapped["SQLPlan"] = relationship(back_populates="tasks")
    attempts: Mapped[list["SQLCaptureTaskAttempt"]] = relationship(
        back_populates="task",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SQLCaptureTaskAttempt.attempted_at",
    )


class SQLCaptureTaskAttempt(SQLBase):
    """SQLAlchemy model for capture task attempts."""

    __tablename__ = "capture_task_attempt"
    __table_args__ = (
        CheckConstraint(
            "attempted_at_theta >= 0 AND attempted_at_theta < 360",
            name="check_attempted_at_theta_range",
        ),
    )

    attempt_id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("capture_task.task_id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[CaptureAttemptStatus] = mapped_column(
        SAEnum(
            CaptureAttemptStatus,
            name="capture_attempt_status",
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
        ),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempted_at_theta: Mapped[float | None] = mapped_column(nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    task: Mapped["SQLCaptureTask"] = relationship(back_populates="attempts")
