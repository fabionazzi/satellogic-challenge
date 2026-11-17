from dataclasses import dataclass
from typing import TypeAlias

Seed: TypeAlias = int | float | str


@dataclass(frozen=True)
class SatelliteSpec:
    satellite_id: int
    name: str
    initial_position: int
    angular_velocity: int
    capture_tolerance: int
    slew_distance: int
    failure_probability: float
    random_seed: Seed
