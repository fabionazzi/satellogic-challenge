from logging import getLogger
from typing import Callable

from src.application.events import (
    PLAN_COMPLETED,
    PLAN_IN_PROGRESS,
    TASK_ATTEMPT,
    TASK_IN_PROGRESS,
    SimulationEvent,
)
from src.application.exceptions import ExecutionPlanDispatchFailed
from src.application.ports.orbit_execution_engine import (
    OrbitExecutionService,
)
from src.application.unit_of_work import CaptureUOW
from src.domain.aggregates.capture import Capture, CaptureStatus
from src.domain.aggregates.plan import Plan
from src.domain.services.scheduler import Scheduler

logger = getLogger(__name__)


class DispatchSimulationUseCase:
    """Use case for scheduling captures for next simulation execution"""

    def __init__(
        self,
        uow: CaptureUOW,
        orbit_service: OrbitExecutionService,
        scheduler: Scheduler,
    ) -> None:
        self._uow = uow
        self._orbit_service = orbit_service
        self._scheduler = scheduler

    async def execute(self) -> Plan | None:
        async with self._uow:
            await self._uow.planner_lock.reject_if_plan_active()

        satellites = await self._orbit_service.get_constellation()

        async with self._uow:
            await self._uow.planner_lock.acquire()
            repository = self._uow.capture_repository
            queued = await repository.all_by_status(CaptureStatus.QUEUED)
            if not queued:
                logger.info("No queued captures to schedule")
                return None

            result = self._scheduler.schedule(
                satellites, list(queued.values())
            )

            to_schedule = [
                queued[task.request_id]
                for assignment in result.scheduled
                for task in assignment.tasks
            ]
            if not to_schedule:
                logger.info("No captures could be scheduled")
                await self._reject(queued, result.rejected)
                return None

            for capture in to_schedule:
                capture.transition_to(CaptureStatus.SCHEDULED)
            scheduled = await repository.update_many(to_schedule)

            plan = await self._uow.plan_repository.add(
                Plan.create([capture.capture_id for capture in scheduled])
            )
            await self._uow.planner_lock.bind(plan.plan_id)

        try:
            await self._orbit_service.dispatch(
                plan.plan_uuid, result.scheduled
            )
        except ExecutionPlanDispatchFailed:
            logger.warning(f"Dispatch of plan {plan.plan_uuid} failed")
            await self._recover(plan, scheduled)
            raise

        async with self._uow:
            refreshed_plan = await self._uow.plan_repository.get_by_uuid(
                plan.plan_uuid
            )
            refreshed_plan.dispatch()
            refreshed_plan = await self._uow.plan_repository.update(
                refreshed_plan
            )
            await self._reject(queued, result.rejected)

        return plan

    async def _reject(
        self, queued: dict[str, Capture], request_ids: list[str]
    ) -> None:
        """Mark the given queued captures as rejected."""
        rejected = [queued[request_id] for request_id in request_ids]
        for capture in rejected:
            capture.transition_to(CaptureStatus.REJECTED)
        await self._uow.capture_repository.update_many(rejected)

    async def _recover(self, plan: Plan, scheduled: list[Capture]) -> None:
        """Mark the plan as dispatch failed and requeue its captures."""
        async with self._uow:
            plan.dispatch_failed()
            await self._uow.plan_repository.update(plan)
            await self._uow.planner_lock.release(plan.plan_id)

            for capture in scheduled:
                capture.requeue()
            await self._uow.capture_repository.update_many(scheduled)


class ProcessSimulationEventUseCase:
    """Responsible for processing simulator event"""

    def __init__(self, uow_factory: Callable[[], CaptureUOW]) -> None:
        self._uow_factory = uow_factory
        self._handlers: dict[str, Callable[[SimulationEvent], None]] = {
            PLAN_IN_PROGRESS: self._handle_plan_in_progress,
            PLAN_COMPLETED: self._handle_plan_completed,
            TASK_IN_PROGRESS: self._handle_task_in_progress,
            TASK_ATTEMPT: self._handle_task_attempt,
        }

    async def execute(self, event: SimulationEvent):
        handler = self._handlers.get(event.name)
        if not handler:
            logger.warning("No handler for event: %s", event.name)
            return
        await handler(event)

    async def _handle_plan_in_progress(self, event: SimulationEvent):
        async with self._uow_factory() as uow:
            plan_uuid = event.payload.plan_uuid
            plan = await uow.plan_repository.get_by_uuid(plan_uuid)
            plan.start(event.occurred_at)
            await uow.plan_repository.update(plan)

    async def _handle_plan_completed(self, event: SimulationEvent):
        async with self._uow_factory() as uow:
            plan_uuid = event.payload.plan_uuid
            plan = await uow.plan_repository.get_by_uuid(plan_uuid)
            plan.complete(event.occurred_at)
            await uow.plan_repository.update(plan)
            captures = await uow.capture_repository.get_by_plan_uuid(plan_uuid)
            to_update = list()
            for capture in captures:
                if capture.not_completed():
                    capture.fail()
                    to_update.append(capture)
            await uow.capture_repository.update_many(to_update)
            await uow.planner_lock.release(plan.plan_id)

    async def _handle_task_in_progress(self, event: SimulationEvent):
        async with self._uow_factory() as uow:
            request_id = event.payload.request_id
            capture = await uow.capture_repository.get_by_request_id(
                request_id
            )
            capture.start()
            await uow.capture_repository.update(capture)

    async def _handle_task_attempt(self, event: SimulationEvent):
        async with self._uow_factory() as uow:
            request_id = event.payload.request_id
            capture = await uow.capture_repository.get_by_request_id(
                request_id
            )
            attempt = event.payload.attempt
            capture.record_attempt(
                status=attempt.status,
                satellite=attempt.satellite_name,
                theta=attempt.attempted_at_theta,
                at=attempt.attempted_at,
                reason=attempt.reason,
            )
            await uow.capture_repository.update(capture)
