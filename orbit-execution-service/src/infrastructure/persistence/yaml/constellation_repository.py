from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from src.domain.repositories.constellation_repository import (
    ConstellationRepository,
)
from src.domain.value_objects.satellite_spec import SatelliteSpec, Seed


class _SatelliteSchema(BaseModel):
    """Internal satellite spec schema. Only for validation"""

    satellite_id: int = Field(alias="id")
    name: str
    initial_position: int = Field(ge=0, lt=360)
    angular_velocity: int = Field(gt=0)
    capture_tolerance: int = Field(ge=0)
    slew_distance: int = Field(ge=0)
    failure_probability: float = Field(ge=0, le=1)
    random_seed: Seed


class _ConstellationSchema(BaseModel):
    """Internal constellation schema. Only for validation"""

    satellites: list[_SatelliteSchema]


class YamlConstellationRepository(ConstellationRepository):
    """Read-only repository backed by a YAML file, loaded once at startup."""

    def __init__(self, path: Path) -> None:
        raw = yaml.safe_load(path.read_text())
        parsed = _ConstellationSchema.model_validate(raw)
        self._specs = {
            sat.satellite_id: SatelliteSpec(
                satellite_id=sat.satellite_id,
                name=sat.name,
                initial_position=sat.initial_position,
                angular_velocity=sat.angular_velocity,
                capture_tolerance=sat.capture_tolerance,
                slew_distance=sat.slew_distance,
                failure_probability=sat.failure_probability,
                random_seed=sat.random_seed,
            )
            for sat in parsed.satellites
        }

    def get_all(self) -> list[SatelliteSpec]:
        return list(self._specs.values())
