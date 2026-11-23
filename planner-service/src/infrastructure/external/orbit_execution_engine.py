from uuid import UUID

import httpx
from pydantic import ValidationError

from src.application.exceptions import (
    ConstellationNotAvailable,
    ExecutionPlanDispatchFailed,
    InvalidSatelliteSpecifications,
)
from src.application.ports.orbit_execution_engine import OrbitExecutionService
from src.domain.value_objects.satellite import Satellite, SatelliteAssignment
from src.infrastructure.external.schemas import (
    ConstellationResponseDTO,
    ExecutionPlanRequestDTO,
)


class HTTPOrbitExecutionService(OrbitExecutionService):
    CONSTELLATION_ENDPOINT = "constellation"
    PLANS_ENDPOINT = "plans/{plan_uuid}"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def dispatch(
        self, plan_uuid: UUID, plan: list[SatelliteAssignment]
    ) -> None:
        body = ExecutionPlanRequestDTO.from_domain(plan=plan)
        try:
            response = await self._client.put(
                self.PLANS_ENDPOINT.format(plan_uuid=plan_uuid),
                json=body.model_dump(mode="json"),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExecutionPlanDispatchFailed from exc

    async def get_constellation(self) -> list[Satellite]:
        try:
            response = await self._client.get(self.CONSTELLATION_ENDPOINT)
            response.raise_for_status()
            constellation = ConstellationResponseDTO.model_validate(
                response.json()
            )
        except httpx.HTTPError as exc:
            raise ConstellationNotAvailable from exc
        except ValidationError as exc:
            raise InvalidSatelliteSpecifications from exc
        return [
            satellite.to_domain() for satellite in constellation.satellites
        ]
