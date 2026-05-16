"""Domain exceptions for DeltaGrid.

Centralized exception types for consistent error handling across the app.
"""


class DeltaGridException(Exception):
    """Base exception for all domain errors."""
    pass


class AuthenticationError(DeltaGridException):
    """Raised when authentication fails (bad credentials, expired token, etc.)."""
    pass


class AuthorizationError(DeltaGridException):
    """Raised when a user lacks permission for an action."""
    pass


class NotFoundError(DeltaGridException):
    """Raised when a requested resource does not exist."""
    pass


class ConflictError(DeltaGridException):
    """Raised when a resource conflict occurs (duplicate email, etc.)."""
    pass


class ValidationError(DeltaGridException):
    """Raised when input validation fails at the domain level."""
    pass
