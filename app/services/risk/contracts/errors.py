"""Redacted coded exception for Risk boundaries."""

import re

from app.services.risk.contracts.enums import RiskErrorCode  # noqa: TC001
from app.utils import HaruQuantError, is_sensitive_key, logger, redact_text_value

_SAFE_DETAIL = re.compile(r"[^A-Z0-9_]+")
_ASSIGNMENT = re.compile(r"(?i)(\b[a-z][a-z0-9_-]*\b\s*[:=]\s*)([^\s,;]+)")


def _redact_assignment(match: re.Match[str]) -> str:
    """Redact values assigned to secret-like keys.

    Args:
        match: Candidate key-value assignment.

    Returns:
        Original assignment or its redacted equivalent.
    """
    logger.debug("Checking Risk error detail assignment for protected data")
    prefix = match.group(1)
    key = re.split(r"\s*[:=]", prefix, maxsplit=1)[0]
    if is_sensitive_key(key):
        return f"{prefix}[REDACTED]"
    return match.group(0)


class RiskDomainError(HaruQuantError):
    """Risk failure carrying a stable code and bounded safe detail.

    Attributes:
        risk_code: Typed Risk error code.
        details: Redacted human-readable diagnostic.
    """

    def __init__(self, code: RiskErrorCode, details: str) -> None:
        """Initialize a redacted Risk failure.

        Args:
            code: Stable Risk error code.
            details: Diagnostic text to redact and bound.
        """
        logger.error("Creating redacted Risk domain failure: %s", code.value)
        redacted = str(redact_text_value(details).value)
        redacted = _ASSIGNMENT.sub(_redact_assignment, redacted)
        self.risk_code = code
        self.details = redacted
        token = _SAFE_DETAIL.sub("_", redacted.upper()).strip("_")
        safe_token = f"DETAIL_{token}"[:128] if token else "RISK_DOMAIN_ERROR"
        super().__init__(code.value, safe_token)


__all__ = ["RiskDomainError"]
