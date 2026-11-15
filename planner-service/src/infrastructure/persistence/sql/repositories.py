from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.aggregates.capture import Capture
from src.domain.entities.capture_attempt import CaptureAttempt
from src.infrastructure.persistence.sql.models import (
    SQLCapture,
    SQLCaptureAttempt,
)


class CaptureORMMapper:
    """Mapper class to convert between SQLAlchemy models and domain entities."""

    @staticmethod
    def to_domain(capture_model: SQLCapture) -> Capture:
        """Convert a SQLAlchemy Capture model to a domain Capture entity."""
        attempts = [
            CaptureAttempt(
                attempt_id=attempt.attempt_id,
                status=attempt.status,
                assigned_satellite=attempt.assigned_satellite,
                attempted_at_theta=attempt.attempted_at_theta,
                attempted_at=attempt.attempted_at,
            )
            for attempt in capture_model.attempts
        ]
        return Capture(
            capture_id=capture_model.capture_id,
            request_id=capture_model.request_id,
            target_name=capture_model.target_name,
            target_theta=capture_model.target_theta,
            priority=capture_model.priority,
            status=capture_model.status,
            attempts=attempts,
        )

    @staticmethod
    def to_orm(capture: Capture) -> SQLCapture:
        """Convert a domain Capture entity to a SQLAlchemy Capture model."""
        capture_model = SQLCapture(
            capture_id=capture.capture_id,
            request_id=capture.request_id,
            target_name=capture.target_name,
            target_theta=capture.target_theta,
            priority=capture.priority,
            status=capture.status,
        )
        for attempt in capture.attempts:
            capture_attempt_model = SQLCaptureAttempt(
                attempt_id=attempt.attempt_id,
                status=attempt.status,
                assigned_satellite=attempt.assigned_satellite,
                attempted_at_theta=attempt.attempted_at_theta,
                attempted_at=attempt.attempted_at,
                capture=capture_model,
            )
            capture_model.attempts.append(capture_attempt_model)
        return capture_model


class SQLCaptureRepository:
    """Repository for managing SQLAlchemy Capture entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, capture: SQLCapture) -> Capture:
        """Add a new capture to the database."""
        self.session.add(capture)
        await self.session.flush()
        return capture

    async def get_by_id(self, capture_id: int) -> Capture | None:
        """Retrieve a capture by its ID."""
        result = await self.session.get(SQLCapture, capture_id)
        return result
