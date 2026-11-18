from collections.abc import Iterable
from uuid import UUID


class InvalidThetaError(Exception):
    """Raised when try to set an invalid angle value"""


class StatusTransitionError(Exception):
    """Raised during invalid state transition"""


class PlanAlreadyExistsError(Exception):
    """Raised when tries to create a plan with same uuid"""

    def __init__(self, plan_uuid: UUID):
        super().__init__(f"Plan {plan_uuid} already exists")
        self.plan_uuid = plan_uuid


class PlanNotFoundError(Exception):
    """Raised when a plan with the given uuid does not exist"""

    def __init__(self, plan_uuid: UUID):
        super().__init__(f"Plan {plan_uuid} not found")
        self.plan_uuid = plan_uuid


class UnknownSatelliteError(Exception):
    """Raised when a plan references satellites not in the constellation"""

    def __init__(self, satellite_ids: Iterable[int]):
        self.satellite_ids = sorted(set(satellite_ids))
        super().__init__(f"Unknown satellites: {self.satellite_ids}")


class NotPersistedError(Exception):
    """Raised when try to access a non-persisted entity"""


class ExecutionInProgressError(Exception):
    """Raised when a plan is submitted while another one is active"""
