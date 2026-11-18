import asyncio
import logging
from collections import defaultdict
from uuid import UUID

from src.application.events import (
    EventFactory,
    SimulationEvent,
)
from src.application.ports.event_publisher import EventPublisher
from src.application.unit_of_work import ExecutionUOWFactory
from src.domain.aggregates.capture_task import CaptureTask
from src.domain.aggregates.plan import Plan
from src.domain.exceptions import PlanNotFoundError
from src.domain.repositories.constellation_repository import (
    ConstellationRepository,
)
from src.domain.satellite import Satellite
from src.domain.value_objects.capture import CaptureResult, CaptureTarget

logger = logging.getLogger(__name__)

SIMULATION_TICKS = 360


class RunSimulationUseCase:
    """Simulate a plan for a fixed number of ticks"""

    def __init__(
        self,
        uow_factory: ExecutionUOWFactory,
        publisher: EventPublisher,
        constellation_repository: ConstellationRepository,
        tick_seconds: float,
    ) -> None:
        self._uow_factory = uow_factory
        self._publisher = publisher
        self._constellation = constellation_repository
        self._tick_seconds = tick_seconds

    async def execute(self, plan_uuid: UUID) -> None:
        plan, tasks = await self._start(plan_uuid)
        if plan is None:
            return

        event = EventFactory.create_plan_event(plan)
        await self._publish_event(event)

        for task in tasks:
            await self._publish_event(
                EventFactory.create_task_started_event(plan, task)
            )

        satellites = self._build_satellites(tasks)
        for _ in range(SIMULATION_TICKS):
            results: list[CaptureResult] = []
            for satellite in satellites:
                result = satellite.execute()
                if result is not None:
                    results.append(result)
                satellite.move()
            if results:
                await self._record(plan, results)
            await asyncio.sleep(self._tick_seconds)

        self._log_unreached(plan, satellites)
        await self._complete(plan)

    async def _start(
        self, plan_uuid: UUID
    ) -> tuple[Plan | None, list[CaptureTask]]:
        async with self._uow_factory() as uow:
            plan = await uow.plans.get_by_uuid(plan_uuid)
            if plan is None:
                raise PlanNotFoundError(plan_uuid)
            if not plan.is_pending():
                logger.warning(
                    "Plan %s is %s, skipping", plan_uuid, plan.status
                )
                return None, []
            tasks = await uow.tasks.list_by_plan(plan.plan_id)
            plan.start()
            await uow.plans.update(plan)
            for task in tasks:
                task.start()
                await uow.tasks.update(task)
        return plan, tasks

    def _build_satellites(self, tasks: list[CaptureTask]) -> list[Satellite]:
        specs = {
            spec.satellite_id: spec for spec in self._constellation.get_all()
        }
        targets: dict[int, list[CaptureTarget]] = defaultdict(list)
        for task in tasks:
            targets[task.satellite_id].append(task.target)
        return [
            Satellite.from_spec(specs[satellite_id], satellite_targets)
            for satellite_id, satellite_targets in targets.items()
        ]

    async def _record(self, plan: Plan, results: list[CaptureResult]) -> None:
        events = []
        async with self._uow_factory() as uow:
            for result in results:
                task = await uow.tasks.get(result.task_id)
                attempt = task.record_attempt(result)
                await uow.tasks.update(task)
                event = EventFactory.create_task_event(plan, task, attempt)
                events.append(event)
        for event in events:
            await self._publish_event(event)

    def _log_unreached(self, plan: Plan, satellites: list[Satellite]) -> None:
        unreached = [t.task_id for s in satellites for t in s.pending_targets]
        if unreached:
            logger.warning(
                "Plan %s: tasks not attempted within %s ticks: %s",
                plan.plan_uuid,
                SIMULATION_TICKS,
                unreached,
            )

    async def _publish_event(self, event: SimulationEvent):
        try:
            await self._publisher.publish(event)
        except Exception:
            logger.exception("Failed to publish %s", event.name)

    async def _complete(self, plan: Plan) -> None:
        async with self._uow_factory() as uow:
            plan.complete()
            await uow.plans.update(plan)
        event = EventFactory.create_plan_event(plan)
        await self._publish_event(event)
