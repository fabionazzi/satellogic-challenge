from typing import Annotated

from fastapi import Depends
from src.application.unit_of_work import CaptureUOW
from src.application.use_cases.capture import (
    CreateCaptureUseCase,
    GetCaptureUseCase,
)
from src.infrastructure.persistence.sql.unit_of_work import (
    SQLCaptureUnitOfWork,
)
from src.presentation.api.v1.dependencies.common import SessionDep


def get_capture_uow(session: SessionDep) -> CaptureUOW:
    return SQLCaptureUnitOfWork(session)


CaptureUOWDep = Annotated[CaptureUOW, Depends(get_capture_uow)]


def get_create_capture_use_case(
    uow: CaptureUOWDep, exec_svc
) -> CreateCaptureUseCase:
    return CreateCaptureUseCase(uow, exec_svc)


def get_get_capture_use_case(uow):
    return GetCaptureUseCase(uow)


CreateCaptureUC = Annotated[
    CreateCaptureUseCase, Depends(get_create_capture_use_case)
]
GetCaptureUC = Annotated[GetCaptureUseCase, Depends(get_get_capture_use_case)]
