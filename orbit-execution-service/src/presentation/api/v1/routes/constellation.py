from fastapi import APIRouter, status
from src.presentation.api.v1.dependencies.constellation import (
    GetConstellationUC,
)
from src.presentation.api.v1.schemas import (
    ConstellationResponse,
    SatelliteSchema,
)

router = APIRouter()


@router.get(
    "",
    summary="Get constellation",
    description="Retrieve the satellites of the constellation.",
    response_model=ConstellationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_constellation(use_case: GetConstellationUC):
    specs = await use_case.execute()
    return ConstellationResponse(
        satellites=[
            SatelliteSchema(
                satellite_id=spec.satellite_id,
                satellite_name=spec.name,
                initial_position=spec.initial_position,
                angular_velocity=spec.angular_velocity,
                capture_tolerance=spec.capture_tolerance,
                slew_distance=spec.slew_distance,
            )
            for spec in specs
        ]
    )
