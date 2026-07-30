"""Private observability validation failures owned by the API domain."""


class ValidationError(ValueError):
    """Raised when metric configuration or evidence is malformed."""


class SecurityError(ValueError):
    """Raised when metric labels attempt to expose sensitive material."""
