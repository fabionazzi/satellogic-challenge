from dataclasses import dataclass


@dataclass(frozen=True)
class CaptureTask:
    request_id: str
    target_theta: float


@dataclass(frozen=True)
class SatelliteAssignment:
    satellite_id: int
    satellite_name: str
    tasks: list[CaptureTask]


@dataclass(frozen=True)
class Satellite:
    """Satellite information"""

    satellite_id: int
    satellite_name: str
    initial_position: int
    angular_velocity: int
    capture_tolerance: int
    slew_distance: int
