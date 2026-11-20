class StatusTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""


class InvalidThetaError(Exception):
    """Raised when an invalid theta value is provided."""


class InvalidPriorityError(Exception):
    """Raised when an invalid priority value is provided."""


class RequestIdAlreadyExistsError(Exception):
    """Raised when a capture with the same request_id already exists."""


class CaptureNotFoundError(Exception):
    """Raised when a capture with the specified ID is not found."""


class NotPersistedError(Exception):
    """Raised when try to access a non-persisted entity"""
