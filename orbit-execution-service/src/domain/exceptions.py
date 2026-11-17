class InvalidThetaError(Exception):
    """Raised when try to set an invalid angle value"""


class StatusTransitionError(Exception):
    """Raised during invalid state transition"""


class PlanAlreadyExistsError(Exception):
    """Raised when tries to create a plan with same uuid"""


class NotPersistedError(Exception):
    """Raised when try to access a non-persisted entity"""
