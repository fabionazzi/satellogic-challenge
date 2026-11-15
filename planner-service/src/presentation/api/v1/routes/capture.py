from fastapi import APIRouter, HTTPException, status
from src.application.exceptions import ExcutionInProgressException
from src.domain.exceptions import RequestIdAlreadyExistsError
from src.presentation.api.v1.dependencies.capture import (
    CreateCaptureUC,
    GetCaptureUC,
)
from src.presentation.api.v1.schemas import (
    CaptureCreateResponse,
    CaptureResponse,
    CreateCaptureRequest,
)

router = APIRouter()


@router.post(
    "",
    summary="Create a new capture",
    description="Create a new capture in the system.",
    response_model=None,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"description": "Invalid input data"},
        409: {
            "description": (
                "Execution in progress, or a capture with "
                "the same request_id already exists"
            )
        },
    },
)
async def create_capture(
    use_case: CreateCaptureUC, request: CreateCaptureRequest
):
    try:
        capture = await use_case.execute(request.to_command())
        return CaptureCreateResponse.from_domain(capture)
    except ExcutionInProgressException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Execution in progress",
        )
    except RequestIdAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Capture with the same request_id already exists",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data",
        )


@router.get(
    "/{capture_id}",
    summary="Get capture by ID",
    description="Retrieve a capture by its ID.",
    response_model=CaptureResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Capture not found"},
    },
)
async def get_capture(capture_id: str, use_case: GetCaptureUC):
    try:
        capture = await use_case.execute(capture_id)
        return CaptureResponse.from_domain(capture)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Capture with ID {capture_id} not found.",
        )
