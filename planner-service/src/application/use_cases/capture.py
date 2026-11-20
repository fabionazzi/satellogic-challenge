from logging import getLogger

from src.application.dto import CreateCaptureCommand
from src.application.unit_of_work import CaptureUOW
from src.domain.aggregates.capture import Capture
from src.domain.exceptions import (
    CaptureNotFoundError,
    RequestIdAlreadyExistsError,
)

logger = getLogger(__name__)


class CreateCaptureUseCase:
    """Use case for creating a new capture."""

    def __init__(self, uow: CaptureUOW):
        self._uow = uow

    async def execute(self, command: CreateCaptureCommand) -> Capture:
        capture = Capture.create(
            command.request_id,
            command.target_name,
            command.target_theta,
            command.priority,
        )
        async with self._uow:
            await self._uow.planner_lock.reject_if_plan_active()
            repository = self._uow.capture_repository
            try:
                new = await repository.add(capture)
                logger.info(
                    f"New capture with request_id {command.request_id} "
                    "created successfully."
                )
                return new
            except RequestIdAlreadyExistsError:
                existing = await repository.get_by_request_id(
                    capture.request_id
                )
                if existing is not None and existing.is_equal(capture):
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
                    raise


class GetCaptureUseCase:
    """Use case for retrieving a capture by its ID."""

    def __init__(self, uow: CaptureUOW):
        self._uow = uow

    async def execute(self, request_id: str) -> Capture:
        async with self._uow:
            capture = await self._uow.capture_repository.get_by_request_id(
                request_id
            )

        if not capture:
            raise CaptureNotFoundError(
                f"Capture with ID {request_id} not found."
            )
        return capture
