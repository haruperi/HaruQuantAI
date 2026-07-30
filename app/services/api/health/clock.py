"""Signed clock-drift diagnostics for readiness probes."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.utils import get_logger, utc_now

logger = get_logger(__name__)

_TOLERANCE_EXCEEDED = "clock tolerance must be positive"

CLOCK_DRIFT_TOLERANCE_SECONDS = Decimal(2)


class _ClockDriftInput(BaseModel):
    """Validation envelope for drift computation inputs."""

    model_config = ConfigDict(extra="forbid")

    reference: datetime
    tolerance_seconds: Decimal

    @field_validator("reference", mode="before")
    @classmethod
    def _validate_reference(cls, value: object) -> datetime:
        """Require UTC-aware timestamps.

        Returns:
            The validated, bounded result.

        Raises:
            TypeError: If reference is not a datetime.
            ValueError: If the declared validation fails.
        """
        if not isinstance(value, datetime):
            raise TypeError("reference must be a datetime")
        if value.tzinfo is None or value.tzinfo.utcoffset(value) != timedelta(0):
            raise ValueError("reference must be aware UTC")
        return value

    @field_validator("tolerance_seconds")
    @classmethod
    def _validate_tolerance(cls, value: Decimal | int | str) -> Decimal:
        """Require a strict positive tolerance.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        typed = Decimal(str(value))
        if typed <= 0:
            raise ValueError(_TOLERANCE_EXCEEDED)
        return typed


def check_clock_drift(
    reference: datetime,
    *,
    tolerance_seconds: Decimal | int | str = CLOCK_DRIFT_TOLERANCE_SECONDS,
) -> Decimal:
    """Return signed local-clock drift from one external authoritative instant.

    Args:
        reference: Authoritative UTC external reference timestamp.
        tolerance_seconds: Allowed absolute drift before readiness degrades.

    Returns:
        Signed delta in seconds of local time minus external reference.

    Raises:
        ValidationError: If reference is naive/non-UTC or tolerance is invalid.

    Raises:
        ValueError: If the declared validation fails.
    """
    values = _ClockDriftInput.model_validate(
        {"reference": reference, "tolerance_seconds": tolerance_seconds},
    )
    if values.tolerance_seconds.is_nan():
        raise ValueError("tolerance_seconds must be a finite decimal")
    now = utc_now()
    drift = Decimal(str((now - values.reference).total_seconds()))
    logger.debug(
        "Clock drift measured; reference=%s tolerance=%s drift=%s",
        values.reference,
        values.tolerance_seconds,
        drift,
    )
    return drift
