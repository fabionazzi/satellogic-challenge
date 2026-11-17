from src.domain.repositories.constellation_repository import (
    ConstellationRepository,
)
from src.domain.value_objects.satellite_spec import SatelliteSpec


class GetConstellationUseCase:
    """Use case for retrieving constellation information."""

    def __init__(self, repository: ConstellationRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[SatelliteSpec]:
        specs = self._repository.get_all()
        return specs
