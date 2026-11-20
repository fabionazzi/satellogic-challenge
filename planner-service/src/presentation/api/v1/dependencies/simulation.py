from typing import Annotated

from fastapi import Depends, Request

from src.application.ports.orbit_execution_engine import (
    OrbitExecutionService,
)
from src.application.use_cases.simulation import DispatchSimulationUseCase
from src.domain.services.scheduler import MockScheduler, Scheduler
from src.presentation.api.v1.dependencies.capture import CaptureUOWDep


def get_orbit_service(request: Request) -> OrbitExecutionService:
    return request.app.state.orbit_service


def get_scheduler() -> Scheduler:
    return MockScheduler()


OrbitServiceDep = Annotated[OrbitExecutionService, Depends(get_orbit_service)]
SchedulerDep = Annotated[Scheduler, Depends(get_scheduler)]


def get_dispatch_simulation_use_case(
    uow: CaptureUOWDep,
    orbit_service: OrbitServiceDep,
    scheduler: SchedulerDep,
) -> DispatchSimulationUseCase:
    return DispatchSimulationUseCase(uow, orbit_service, scheduler)


DispatchSimulationUC = Annotated[
    DispatchSimulationUseCase, Depends(get_dispatch_simulation_use_case)
]
