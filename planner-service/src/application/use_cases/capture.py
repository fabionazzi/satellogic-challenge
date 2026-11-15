from logging import getLogger

from src.application.dto import CreateCaptureCommand
from src.application.exceptions import ExcutionInProgressException
from src.application.ports.execution_service import (
    ExecutionService,
    ExecutionStatus,
)
from src.application.unit_of_work import CaptureUOW
from src.domain.aggregates.capture import Capture
from src.domain.exceptions import (
    CaptureNotFoundError,
    RequestIdAlreadyExistsError,
)

logger = getLogger(__name__)


class CreateCaptureUseCase:
    """Use case for creating a new capture."""

    def __init__(self, uow: CaptureUOW, execution_service: ExecutionService):
        self._uow = uow
        self._execution_service = execution_service

    async def execute(self, command: CreateCaptureCommand) -> Capture:
        status = await self._execution_service.get_status()
        if status == ExecutionStatus.IN_PROGRESS:
            raise ExcutionInProgressException(
                "Cannot create a new capture while execution is in progress."
            )
        capture = Capture.create(
            command.request_id,
            command.target_name,
            command.target_theta,
            command.priority,
        )
        async with self._uow:
            repository = self._uow.capture_repository
            existing = await repository.get_by_request_id(command.request_id)
            if not existing:
                new = await repository.save(capture)
                logger.info(
                    f"New capture with request_id {command.request_id} "
                    "created successfully."
                )
                return new
            elif existing and existing.is_equal(capture):
                logger.info(
                    f"Capture with request_id {command.request_id} already "
                    "exists with the same attributes."
                )
                return existing
            else:
                logger.warning(
                    f"Capture with request_id {command.request_id} already "
                    "exists with different attributes."
                )
                raise RequestIdAlreadyExistsError(
                    f"Capture with request_id {command.request_id} already "
                    "exists."
                )


class GetCaptureUseCase:
    """Use case for retrieving a capture by its ID."""

    def __init__(self, uow: CaptureUOW):
        self._uow = uow

    async def execute(self, capture_id: str) -> Capture:
        async with self._uow:
            capture = await self._uow.capture_repository.get_by_id(capture_id)

        if not capture:
            raise CaptureNotFoundError(
                f"Capture with ID {capture_id} not found."
            )
        return capture
