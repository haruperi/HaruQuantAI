"""Controlled Simulation boundary exception."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from app.services.simulator.errors.catalog import SIM_ERROR_CATALOG
from app.utils import logger, redact_mapping_value, redact_text_value


class SimulationError(Exception):
    """Controlled fail-closed exception at the Simulation boundary.

    Attributes:
        code: Cataloged stable error code.
        message: Bounded safe explanation.
        request_id: Optional safe trace identifier.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize a controlled Simulation error.

        Args:
            code: Cataloged Simulation error code.
            message: Secret-safe explanation.
            details: Optional bounded details to redact.
            request_id: Optional trace identifier.
            correlation_id: Optional correlation identifier.

        Raises:
            ValueError: If the code is absent or text is invalid.
        """
        logger.debug("Creating SimulationError with code %s", code)
        if code not in SIM_ERROR_CATALOG:
            raise ValueError("Simulation error code is not cataloged")
        if not message or message != message.strip():
            raise ValueError("Simulation error message must be non-empty and trimmed")
        for value, field in (
            (request_id, "request_id"),
            (correlation_id, "correlation_id"),
        ):
            if value is not None and (not value or value != value.strip()):
                identity_error = f"{field} must be non-empty and trimmed"
                raise ValueError(identity_error)
        safe_message = str(redact_text_value(message).value)[:512]
        safe_details: Mapping[str, object] = MappingProxyType({})
        if details is not None:
            redacted = redact_mapping_value(details).value
            if not isinstance(redacted, Mapping):
                raise ValueError("Simulation error details must be a mapping")
            safe_details = MappingProxyType(dict(redacted))
        self.code = code
        self.message = safe_message
        self.details = safe_details
        self.request_id = request_id
        self.correlation_id = correlation_id
        super().__init__(self.message)


__all__ = ["SimulationError"]
