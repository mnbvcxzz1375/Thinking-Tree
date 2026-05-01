"""Custom exceptions for the application."""


class AppException(Exception):
    """Base exception for the application."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        """Initialize exception."""
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize exception."""
        super().__init__(message, status_code=404)


class ValidationError(AppException):
    """Exception raised for validation errors."""

    def __init__(self, message: str = "Validation error") -> None:
        """Initialize exception."""
        super().__init__(message, status_code=422)


class DatabaseError(AppException):
    """Exception raised for database errors."""

    def __init__(self, message: str = "Database error") -> None:
        """Initialize exception."""
        super().__init__(message, status_code=500)


class UnauthorizedError(AppException):
    """Exception raised for unauthorized access."""

    def __init__(self, message: str = "Unauthorized") -> None:
        """Initialize exception."""
        super().__init__(message, status_code=401)
