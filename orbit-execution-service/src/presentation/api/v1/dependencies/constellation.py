from typing import Annotated

from fastapi import Depends, Request
from src.application.use_cases.get_constellation import GetConstellationUseCase
from src.domain.repositories.constellation_repository import (
    ConstellationRepository,
)


def get_constellation_repository(request: Request) -> ConstellationRepository:
    return request.app.state.constellation_repository


ConstellationRepositoryDep = Annotated[
    ConstellationRepository, Depends(get_constellation_repository)
]


def get_get_constellation_use_case(
    repository: ConstellationRepositoryDep,
) -> GetConstellationUseCase:
    return GetConstellationUseCase(repository=repository)


GetConstellationUC = Annotated[
    GetConstellationUseCase, Depends(get_get_constellation_use_case)
]
