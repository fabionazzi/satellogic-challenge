from abc import ABC, abstractmethod
from itertools import product

from src.domain.aggregates.capture import Capture
from src.domain.value_objects.satellite import (
    CaptureTask,
    Satellite,
    SatelliteAssignment,
)
from src.domain.value_objects.schedule_result import ScheduleResult

Route = tuple[Capture, ...]
Combination = list[tuple[Satellite, Route]]


class Scheduler(ABC):
    """Service responsible for scheduling captures."""

    @abstractmethod
    def schedule(
        self, satellites: list[Satellite], captures: list[Capture]
    ) -> ScheduleResult:
        """Schedule captures"""
        pass


# class MockScheduler(Scheduler):
#     def __init__(self):
#         self._rng = Random(1)

#     def schedule(
#         self, satellites: list[Satellite], captures: list[Capture]
#     ) -> ScheduleResult:
#         rejected = captures.pop()
#         assigned: dict[tuple[int, str], list[CaptureTask]] = dict()

#         for capture in captures:
#             satellite = self._rng.choice(satellites)
#             key = (satellite.satellite_id, satellite.satellite_name)
#             assigned.setdefault(key, [])
#             assigned[key].append(
#                 CaptureTask(
#                     request_id=capture.request_id,
#                     target_theta=capture.target_theta,
#                 )
#             )

#         assignments = [
#             SatelliteAssignment(
#                 satellite_id=s[0],
#                 satellite_name=s[1],
#                 tasks=t,
#             )
#             for s, t in assigned.items()
#         ]

#         return ScheduleResult(
#             rejected=[rejected.request_id], scheduled=assignments
#         )


class ExhaustiveScheduler(Scheduler):
    """Scheduler that evaluates every combination of satellite routes."""

    LIMIT = 360

    def schedule(
        self, satellites: list[Satellite], captures: list[Capture]
    ) -> ScheduleResult:
        routes_per_satellite = [
            self._find_routes(satellite, captures) for satellite in satellites
        ]
        combinations = (
            list(zip(satellites, routes))
            for routes in product(*routes_per_satellite)
            if self._is_disjoint(routes)
        )
        best = min(combinations, key=self._score)

        scheduled = [
            SatelliteAssignment(
                satellite_id=satellite.satellite_id,
                satellite_name=satellite.satellite_name,
                tasks=[
                    CaptureTask(
                        request_id=capture.request_id,
                        target_theta=capture.target_theta,
                    )
                    for capture in route
                ],
            )
            for satellite, route in best
            if route
        ]
        assigned = {
            capture.request_id for _, route in best for capture in route
        }
        rejected = [
            capture.request_id
            for capture in captures
            if capture.request_id not in assigned
        ]
        return ScheduleResult(scheduled=scheduled, rejected=rejected)

    def _offset(self, satellite: Satellite, capture: Capture) -> float:
        return (capture.target_theta - satellite.initial_position) % 360

    def _check(
        self,
        satellite: Satellite,
        current: Capture | None,
        next_capture: Capture,
    ) -> bool:
        offset = self._offset(satellite, next_capture)
        window_start = offset - satellite.capture_tolerance
        window_end = offset + satellite.capture_tolerance
        if window_start < 0 or window_end > self.LIMIT:
            return False
        if current is None:
            return True
        free_at = (
            self._offset(satellite, current)
            + satellite.capture_tolerance
            + satellite.slew_distance
        )
        return free_at <= window_start

    def _create_routes(
        self,
        satellite: Satellite,
        captures: list[Capture],
        current: Capture | None = None,
        route: Route = (),
    ) -> list[Route]:
        routes = [route]
        for i, next_capture in enumerate(captures):
            if self._check(satellite, current, next_capture):
                routes.extend(
                    self._create_routes(
                        satellite,
                        captures[i + 1 :],
                        next_capture,
                        (*route, next_capture),
                    )
                )
        return routes

    def _find_routes(
        self, satellite: Satellite, captures: list[Capture]
    ) -> list[Route]:
        ordered = sorted(captures, key=lambda c: self._offset(satellite, c))
        return self._create_routes(satellite, ordered)

    def _capture_time(self, satellite: Satellite, capture: Capture) -> float:
        return (
            self._offset(satellite, capture) - satellite.capture_tolerance
        ) / satellite.angular_velocity

    def _score(self, combination: Combination) -> tuple:
        captures = [capture for _, route in combination for capture in route]
        return (
            -len(captures),
            sorted(capture.priority for capture in captures),
            sorted(
                self._capture_time(satellite, capture)
                for satellite, route in combination
                for capture in route
            ),
            sorted(capture.request_id for capture in captures),
        )

    def _is_disjoint(self, routes: tuple[Route, ...]) -> bool:
        names = [capture.request_id for route in routes for capture in route]
        return len(names) == len(set(names))
