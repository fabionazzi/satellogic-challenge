from typing import Annotated

from fastapi import Depends, Request
from src.application.ports.event_publisher import EventPublisher
from src.application.ports.simulation_scheduler import SimulationScheduler
from src.application.unit_of_work import ExecutionUOWFactory
from src.application.use_cases.submit_plan import SubmitPlanUseCase
from src.presentation.api.v1.dependencies.constellation import (
    ConstellationRepositoryDep,
)


def get_uow_factory(request: Request) -> ExecutionUOWFactory:
    return request.app.state.uow_factory


def get_event_publisher(request: Request) -> EventPublisher:
    return request.app.state.publisher


def get_simulation_scheduler(request: Request) -> SimulationScheduler:
    return request.app.state.scheduler


UOWFactoryDep = Annotated[ExecutionUOWFactory, Depends(get_uow_factory)]
EventPublisherDep = Annotated[EventPublisher, Depends(get_event_publisher)]
SimulationSchedulerDep = Annotated[
    SimulationScheduler, Depends(get_simulation_scheduler)
]


def get_submit_plan_use_case(
    uow_factory: UOWFactoryDep,
    publisher: EventPublisherDep,
    scheduler: SimulationSchedulerDep,
    constellation_repository: ConstellationRepositoryDep,
) -> SubmitPlanUseCase:
    return SubmitPlanUseCase(
        uow_factory=uow_factory,
        publisher=publisher,
        scheduler=scheduler,
        constellation_repository=constellation_repository,
    )


SubmitPlanUC = Annotated[SubmitPlanUseCase, Depends(get_submit_plan_use_case)]
