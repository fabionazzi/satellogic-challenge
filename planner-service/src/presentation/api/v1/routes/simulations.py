from fastapi import APIRouter, HTTPException, Response, status

from src.application.exceptions import (
    ConstellationNotAvailable,
    ExecutionInProgressException,
    ExecutionPlanDispatchFailed,
    InvalidSatelliteSpecifications,
)
from src.presentation.api.v1.dependencies.simulation import (
    DispatchSimulationUC,
)
from src.presentation.api.v1.schemas import SimulationResponse

router = APIRouter()


@router.post(
    "",
    summary="Dispatch a simulation",
    description="Schedule queued captures and dispatch them for execution.",
    response_model=SimulationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Nothing to schedule"},
        status.HTTP_409_CONFLICT: {"description": "A plan is already active"},
        status.HTTP_502_BAD_GATEWAY: {
            "description": "Orbit execution service failed"
        },
    },
)
async def dispatch_simulation(use_case: DispatchSimulationUC):
    try:
        plan = await use_case.execute()
    except ExecutionInProgressException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A plan is already active",
        )
    except (
        ConstellationNotAvailable,
        InvalidSatelliteSpecifications,
        ExecutionPlanDispatchFailed,
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Orbit execution service unavailable",
        )
    if plan is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return SimulationResponse.from_domain(plan)
