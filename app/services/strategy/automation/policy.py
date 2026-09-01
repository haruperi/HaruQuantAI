"""Automation-mode policy subordinate to external interlocks."""

# mypy: disable-error-code="return-value"

from typing import Literal

from app.composition.logging import get_logger

logger = get_logger(__name__)


def evaluate_automation_mode(
    mode: str,
    *,
    risk_interlock: bool,
    trading_interlock: bool,
    route: str,
    environment: str,
) -> Literal["OFF", "ADVISORY", "SUPERVISED", "AUTOMATED", "RESTRICTED"]:
    """Return the effective mode without overriding safety interlocks.

    Args:
        mode: Requested operational automation mode name.
        risk_interlock: Operational risk interlock status.
        trading_interlock: Operational trading interlock status.
        route: Target execution route identifier.
        environment: Current deployment environment.

    Returns:
        Effective approved automation mode.

    Raises:
        ValueError: If mode is not a known automation mode.
    """
    if mode not in {"OFF", "ADVISORY", "SUPERVISED", "AUTOMATED"}:
        raise ValueError("unknown automation mode")
    if mode in {"OFF", "ADVISORY"}:
        return mode
    if (
        not risk_interlock
        or not trading_interlock
        or route != "SIM"
        or environment == "LIVE"
    ):
        logger.warning("Automation mode restricted by external interlock")
        return "RESTRICTED"
    return mode


__all__ = ["evaluate_automation_mode"]
