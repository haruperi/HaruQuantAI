"""Automation-mode policy subordinate to external interlocks."""

# mypy: disable-error-code="return-value"
# ruff: noqa: DOC501

from typing import Literal

from app.utils import get_logger

logger = get_logger(__name__)


def evaluate_automation_mode(
    mode: str,
    *,
    risk_interlock: bool,
    trading_interlock: bool,
    route: str,
    environment: str,
) -> Literal["OFF", "ADVISORY", "SUPERVISED", "AUTOMATED", "RESTRICTED"]:
    """Return the effective mode without overriding safety interlocks."""
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
