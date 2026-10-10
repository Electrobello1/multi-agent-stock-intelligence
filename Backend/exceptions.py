class UserNotFoundError(Exception):
    """Raised when a user cannot be found."""
    pass


class SessionNotFoundError(Exception):
    """Raised when a chat session cannot be found."""
    pass


class AnalysisNotFoundError(Exception):
    """Raised when an analysis cannot be found."""
    pass


class AuthenticationError(Exception):
    """Raised for authentication failures."""
    pass


class AuthorizationError(Exception):
    """Raised when a user is not authorized."""
    pass


class ValidationError(Exception):
    """Raised when validation fails."""
    pass

class VectorNotFoundError(Exception):
    """Raised when vector is not found."""
    pass