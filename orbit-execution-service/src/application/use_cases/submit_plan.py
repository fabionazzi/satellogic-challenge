import logging
from uuid import UUID

from src.application.dto import PlanDTO
from src.application.events import EventFactory
from src.application.ports.event_publisher import EventPublisher
from src.application.ports.simulation_scheduler import SimulationScheduler
from src.application.unit_of_work import ExecutionUOWFactory
from src.domain.aggregates.capture_task import CaptureTask
from src.domain.aggregates.plan import Plan
from src.domain.exceptions import PlanAlreadyExistsError, UnknownSatelliteError
from src.domain.repositories.constellation_repository import (
    ConstellationRepository,
)

logger = logging.getLogger(__name__)


class SubmitPlanUseCase:
    """Persist a new plan and schedule its simulation"""

    def __init__(
        self,
        uow_factory: ExecutionUOWFactory,
        publisher: EventPublisher,
        scheduler: SimulationScheduler,
        constellation_repository: ConstellationRepository,
    ) -> None:
        self._uow_factory = uow_factory
        self._publisher = publisher
        self._scheduler = scheduler
        self._constellation = constellation_repository

    async def execute(self, plan_uuid: UUID, plan_dto: PlanDTO) -> Plan:
        self._validate_satellites(plan_dto)

        async with self._uow_factory() as uow:
            if await uow.plans.get_by_uuid(plan_uuid) is not None:
                raise PlanAlreadyExistsError(plan_uuid)
            plan = await uow.plans.add(Plan.create(plan_uuid))
            await uow.tasks.add_many(
                [
                    CaptureTask.create(
                        plan_id=plan.plan_id,
                        request_id=task.request_id,
                        satellite_id=assignment.satellite_id,
                        target_theta=task.target_theta,
                    )
                    for assignment in plan_dto.assignments
                    for task in assignment.tasks
                ]
            )

        event = EventFactory.create_plan_event(plan)
        try:
            await self._publisher.publish(event)
        except Exception:
            logger.exception("Failed to publish %s", event.name)
        await self._scheduler.schedule(plan_uuid)
        return plan

    def _validate_satellites(self, plan_dto: PlanDTO) -> None:
        known = {spec.satellite_id for spec in self._constellation.get_all()}
        requested = {
            assignment.satellite_id for assignment in plan_dto.assignments
        }
        if unknown := requested - known:
            raise UnknownSatelliteError(unknown)
