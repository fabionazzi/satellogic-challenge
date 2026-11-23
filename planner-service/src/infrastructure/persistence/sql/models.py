from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
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

from src.domain.aggregates.plan import PlanStatus
from src.domain.capture_status import CaptureAttemptStatus, CaptureStatus


class SQLBase(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin class for timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SQLCapture(SQLBase, TimestampMixin):
    """SQLAlchemy model for captures."""

    __tablename__ = "capture"
    __table_args__ = (
        Index("ix_capture_status", "status"),
        UniqueConstraint("request_id", name="uq_capture_request_id"),
        CheckConstraint("priority >= 0", name="check_priority_non_negative"),
        CheckConstraint(
            "target_theta >= 0 AND target_theta < 360",
            name="check_target_theta_range",
        ),
    )

    capture_id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    target_name: Mapped[str] = mapped_column(String(64), nullable=False)
    target_theta: Mapped[float] = mapped_column(nullable=False)
    priority: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[CaptureStatus] = mapped_column(
        SAEnum(
            CaptureStatus,
            name="capture_status",
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
        ),
        default=CaptureStatus.QUEUED,
    )

    attempts: Mapped[list["SQLCaptureAttempt"]] = relationship(
        back_populates="capture",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SQLCaptureAttempt.attempted_at",
    )


class SQLCaptureAttempt(SQLBase):
    """SQLAlchemy model for capture attempts."""

    __tablename__ = "capture_attempt"

    attempt_id: Mapped[int] = mapped_column(primary_key=True)
    capture_id: Mapped[int] = mapped_column(
        ForeignKey("capture.capture_id", ondelete="CASCADE"), nullable=False
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
    assigned_satellite: Mapped[str] = mapped_column(String(64), nullable=False)
    attempted_at_theta: Mapped[float] = mapped_column(nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )

    capture: Mapped["SQLCapture"] = relationship(back_populates="attempts")


class SQLPlan(SQLBase):
    """SQLAlchemy model for plans"""

    __tablename__ = "plan"
    __table_args__ = (UniqueConstraint("plan_uuid", name="uq_plan_uuid"),)

    plan_id: Mapped[int] = mapped_column(primary_key=True)
    plan_uuid: Mapped[UUID] = mapped_column(nullable=False)
    status: Mapped[PlanStatus] = mapped_column(
        SAEnum(
            PlanStatus,
            name="plan_status",
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
        ),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    capture_links: Mapped[list["SQLPlanCapture"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )


class SQLPlannerLock(SQLBase):
    """Single-row lock held while a plan is active"""

    __tablename__ = "planner_lock"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_planner_lock_singleton"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    active_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("plan.plan_id", ondelete="SET NULL"), nullable=True
    )


class SQLPlanCapture(SQLBase):
    """Association table for plans and captures"""

    __tablename__ = "plan_capture"
    __table_args__ = (Index("ix_plan_capture_capture_id", "capture_id"),)

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plan.plan_id", ondelete="CASCADE"), primary_key=True
    )
    capture_id: Mapped[int] = mapped_column(
        ForeignKey("capture.capture_id", ondelete="CASCADE"), primary_key=True
    )
