from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from src.domain.exceptions import (
    ExecutionInProgressError,
    PlanAlreadyExistsError,
    UnknownSatelliteError,
)
from src.presentation.api.v1.dependencies.plan import SubmitPlanUC
from src.presentation.api.v1.schemas import (
    CreatePlanRequest,
    PlanAcceptedResponse,
)

router = APIRouter()


@router.put(
    "/{plan_id}",
    summary="Submit a plan for execution",
    description="Persist the plan and start its simulation in the background.",
    response_model=PlanAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Plan already exists or execution in progress"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Invalid plan or unknown satellites"
        },
    },
)
async def submit_plan(
    plan_id: UUID,
    request: CreatePlanRequest,
    use_case: SubmitPlanUC,
):
    try:
        plan = await use_case.execute(plan_id, request.to_dto())
    except PlanAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Plan already exists"
        ) from exc
    except UnknownSatelliteError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unknown satellites",
        ) from exc
    except ExecutionInProgressError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Execution in progress",
        ) from exc
    return PlanAcceptedResponse.from_domain(plan)
