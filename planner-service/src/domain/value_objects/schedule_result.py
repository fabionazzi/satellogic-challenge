from dataclasses import dataclass

from src.domain.value_objects.satellite import SatelliteAssignment


@dataclass(frozen=True)
class ScheduleResult:
    scheduled: list[SatelliteAssignment]
    rejected: list[str]
