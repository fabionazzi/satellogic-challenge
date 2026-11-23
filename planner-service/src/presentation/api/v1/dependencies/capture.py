from typing import Annotated

from fastapi import Depends, Request

from src.application.unit_of_work import CaptureUOW
from src.application.use_cases.capture import (
    CreateCaptureUseCase,
    GetCaptureUseCase,
)
from src.infrastructure.persistence.sql.unit_of_work import (
    SQLCaptureUnitOfWork,
)


def get_capture_uow(request: Request) -> CaptureUOW:
    return SQLCaptureUnitOfWork(request.app.state.sessionmaker)


CaptureUOWDep = Annotated[CaptureUOW, Depends(get_capture_uow)]


def get_create_capture_use_case(uow: CaptureUOWDep) -> CreateCaptureUseCase:
    return CreateCaptureUseCase(uow)


def get_get_capture_use_case(uow: CaptureUOWDep) -> GetCaptureUseCase:
    return GetCaptureUseCase(uow)


CreateCaptureUC = Annotated[
    CreateCaptureUseCase, Depends(get_create_capture_use_case)
]
GetCaptureUC = Annotated[GetCaptureUseCase, Depends(get_get_capture_use_case)]
