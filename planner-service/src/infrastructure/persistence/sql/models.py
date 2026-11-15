from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from src.domain.capture_status import CaptureAttemptStatus, CaptureStatus


class Base(DeclarativeBase):
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


class SQLCapture(Base, TimestampMixin):
    """SQLAlchemy model for captures."""

    __tablename__ = "capture"
    __table_args__ = (
        CheckConstraint("priority >= 0", name="check_priority_non_negative"),
        CheckConstraint(
            "target_theta >= 0 AND target_theta < 360",
            name="check_target_theta_range",
        ),
    )

    capture_id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    target_name: Mapped[str] = mapped_column(nullable=False)
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


class SQLCaptureAttempt(Base):
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
    assigned_satellite: Mapped[str] = mapped_column(nullable=False)
    attempted_at_theta: Mapped[float] = mapped_column(nullable=False)
    details: Mapped[str | None] = mapped_column(nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )

    capture: Mapped["SQLCapture"] = relationship(back_populates="attempts")
