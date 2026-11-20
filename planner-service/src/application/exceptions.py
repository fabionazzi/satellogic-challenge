class ExecutionInProgressException(Exception):
    """Raised when an execution is already in progress."""


class ExecutionPlanDispatchFailed(Exception):
    """Raised when fails to send an execution plan"""


class ConstellationNotAvailable(Exception):
    """Raised when constellation cannot be obtained"""


class InvalidSatelliteSpecifications(Exception):
    """Raised when constellation information is malformed"""
