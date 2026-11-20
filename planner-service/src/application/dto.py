from dataclasses import dataclass

from src.domain.value_objects.satellite import Satellite


@dataclass(frozen=True)
class CreateCaptureCommand:
    """Command to create a new capture."""

    request_id: str
    target_name: str
    target_theta: float
    priority: int


@dataclass(frozen=True)
class SatelliteDTO:
    """Satellite information"""

    satellite_id: int
    satellite_name: str
    initial_position: int
    angular_velocity: int
    capture_tolerance: int
    slew_distance: int

    def to_domain(self) -> Satellite:
        return Satellite(
            satellite_id=self.satellite_id,
            satellite_name=self.satellite_name,
            initial_position=self.initial_position,
            angular_velocity=self.angular_velocity,
            capture_tolerance=self.capture_tolerance,
            slew_distance=self.slew_distance,
        )
