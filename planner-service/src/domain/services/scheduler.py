from abc import ABC, abstractmethod

from src.domain.aggregates.capture import Capture
from src.domain.value_objects.satellite import Satellite
from src.domain.value_objects.schedule_result import ScheduleResult


class Scheduler(ABC):
    """Service responsible for scheduling captures."""

    @abstractmethod
    def schedule(
        self, satellites: list[Satellite], captures: list[Capture]
    ) -> ScheduleResult:
        """Schedule captures"""
        pass


from random import Random

from src.domain.value_objects.satellite import CaptureTask, SatelliteAssignment


class MockScheduler(Scheduler):
    def __init__(self):
        self._rng = Random(1)

    def schedule(
        self, satellites: list[Satellite], captures: list[Capture]
    ) -> ScheduleResult:
        rejected = captures.pop()
        assigned: dict[tuple[int, str], list[CaptureTask]] = dict()

        for capture in captures:
            satellite = self._rng.choice(satellites)
            key = (satellite.satellite_id, satellite.satellite_name)
            assigned.setdefault(key, [])
            assigned[key].append(
                CaptureTask(
                    request_id=capture.request_id,
                    target_theta=capture.target_theta,
                )
            )

        assignments = [
            SatelliteAssignment(
                satellite_id=s[0],
                satellite_name=s[1],
                tasks=t,
            )
            for s, t in assigned.items()
        ]

        return ScheduleResult(
            rejected=[rejected.request_id], scheduled=assignments
        )
