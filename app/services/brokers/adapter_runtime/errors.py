"""Private canonical transport-control exceptions."""


class _RequestValidationError(ValueError):
    """Canonical request failed before provider transmission."""


class _ProviderResponseError(ValueError):
    """Provider response lacked mandatory canonical evidence."""


class _CircuitOpenError(ConnectionError):
    """Circuit rejected a provider call before transmission."""


class _RateLimitedError(ConnectionError):
    """Rate policy rejected a provider call before transmission."""
