import random
from datetime import UTC, datetime

from src.domain.value_objects.capture import (
    CaptureAttemptStatus,
    CaptureOutcome,
    CaptureResult,
    CaptureTarget,
)
from src.domain.value_objects.satellite_spec import SatelliteSpec, Seed

CAPTURE_ERROR_REASONS = [
    "OPTICAL_PAYLOAD_LOCK_TIMEOUT",
    "ADCS_POINTING_TOLERANCE_EXCEEDED",
    "EPS_BATTERY_VOLTAGE_LOW",
    "THERMAL_SENSOR_TEMPERATURE_OUT_OF_RANGE",
    "OBC_STORAGE_BUFFER_FULL",
]


class SatelliteOutputGenerator:
    """Create mock output for satellite capture attempt"""

    def __init__(self, failure_probability: float, seed: Seed | None = None):
        self._failure_probability = failure_probability
        self._generator = random.Random(seed)

    def generate(self) -> CaptureOutcome:
        result = self._generator.random()
        if result < self._failure_probability:
            return CaptureOutcome(
                status=CaptureAttemptStatus.FAILED,
                reason=self._generator.choice(CAPTURE_ERROR_REASONS),
            )
        return CaptureOutcome(status=CaptureAttemptStatus.SUCCEEDED)


class Satellite:
    """Satellite representation"""

    def __init__(
        self,
        satellite_id: int,
        name: str,
        initial_position: int,
        angular_velocity: int,
        capture_tolerance: int,
        slew_distance: int,
        targets: list[CaptureTarget],
        output_generator: SatelliteOutputGenerator,
    ) -> None:
        self._id = satellite_id
        self._name = name
        self._current_position = initial_position
        self._angular_velocity = angular_velocity
        self._capture_tolerance = capture_tolerance
        self._slew_distance = slew_distance
        self._available_after = 0
        self._output_generator = output_generator
        self._pending_targets = list(targets)

    def _forward_distance(self, target_theta: float) -> float:
        """Degrees the satellite must still travel before it can
        capture target_theta."""
        reference = (
            self._current_position
            + self._available_after
            - self._capture_tolerance
        )
        return (target_theta - reference) % 360

    def _select_next_task(self) -> CaptureTarget:
        """Select next task for execution."""
        task = min(
            self._pending_targets,
            key=lambda t: self._forward_distance(t.target_theta),
        )
        return task

    def _can_capture(self, target_theta: float) -> bool:
        """Evaluates if d(a,b) <= capture tolerance"""
        diff = abs(self._current_position - target_theta)
        distance = min(diff, 360 - diff)
        return distance <= self._capture_tolerance

    def _capture(self) -> CaptureOutcome:
        """Execute a simulated capture"""
        return self._output_generator.generate()

    def _is_available(self) -> bool:
        """Check if the satellite is ready for a new capture."""
        return self._available_after == 0

    @classmethod
    def from_spec(
        cls, spec: SatelliteSpec, targets: list[CaptureTarget]
    ) -> "Satellite":
        return cls(
            satellite_id=spec.satellite_id,
            name=spec.name,
            initial_position=spec.initial_position,
            angular_velocity=spec.angular_velocity,
            capture_tolerance=spec.capture_tolerance,
            slew_distance=spec.slew_distance,
            targets=targets,
            output_generator=SatelliteOutputGenerator(
                spec.failure_probability, spec.random_seed
            ),
        )

    def move(self):
        """Move to the next position."""
        self._current_position = (
            self._current_position + self._angular_velocity
        ) % 360
        self._available_after = max(
            self._available_after - self._angular_velocity, 0
        )

    def execute(self) -> CaptureResult | None:
        """Execute the closest reachable task"""
        if not self.has_pending_tasks or not self._is_available():
            return None
        task = self._select_next_task()
        if not self._can_capture(task.target_theta):
            return None
        # NOTE: Assumed only one attempt but it could retry as long as
        # the satellite remains within the capture tolerance angle
        self._pending_targets.remove(task)
        self._available_after = self._slew_distance
        result = self._capture()
        return CaptureResult(
            satellite_id=self._id,
            satellite_name=self._name,
            task_id=task.task_id,
            attempted_at_theta=self._current_position,
            attempted_at=datetime.now(UTC),
            status=result.status,
            reason=result.reason,
        )

    @property
    def has_pending_tasks(self) -> bool:
        return len(self._pending_targets) > 0

    @property
    def pending_targets(self) -> list[CaptureTarget]:
        return list(self._pending_targets)
