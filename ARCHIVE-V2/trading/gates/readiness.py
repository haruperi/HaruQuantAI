"""Broker readiness and clock synchronization gate primitives.

This module validates broker connection status, trading allowance, account
permissions, and client-side rate-limit availability without sending any
test orders (TRD-FR-093), validates local clock drift and PTP-aligned
end-to-end latency against configured thresholds (TRD-FR-094, TRD-FR-095),
and exposes a non-mutating live readiness dry run (TRD-FR-096).

Every check consumes explicit caller-supplied evidence rather than calling
the broker or system clock directly, so gate evaluation stays deterministic
and replayable (TRD-NFR-011).
"""
# ruff: noqa: SIM102, TRY301

from __future__ import annotations

from decimal import Decimal

from app.services.trading.contracts import TradingContract
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingValidationError,
)
from app.utils.logger import logger

CLOCK_DRIFT_THRESHOLD_MS = Decimal(50)


class BrokerReadinessEvidence(TradingContract):
    """Broker readiness evidence resolved by the caller (TRD-FR-093).

    Attributes:
        connected: Whether the broker adapter reports an active connection.
        trade_allowed: Whether the broker/account currently allows trading.
        account_permissions_ok: Whether required account permissions hold.
        rate_limit_available: Whether client-side rate-limit capacity is
            available for this request.
    """

    connected: bool
    trade_allowed: bool
    account_permissions_ok: bool
    rate_limit_available: bool


class ClockDriftEvidence(TradingContract):
    """Clock synchronization and PTP latency evidence (TRD-FR-094/095).

    Attributes:
        offset_ms: Local system clock offset versus the broker server time,
            in milliseconds. May be negative; the absolute value is checked.
        ptp_aligned: Whether PTP hardware clock alignment is active.
        ptp_latency_ms: Measured end-to-end hardware latency between the
            PTP-aligned local clock and the quote's wire timestamp, when
            PTP alignment is active and a wire timestamp is present.
        max_ptp_latency_ms: Configured maximum acceptable PTP latency.
    """

    offset_ms: Decimal
    ptp_aligned: bool = False
    ptp_latency_ms: Decimal | None = None
    max_ptp_latency_ms: Decimal | None = None


class ReadinessCheckResult(TradingContract):
    """Non-mutating live readiness dry run outcome (TRD-FR-096).

    Attributes:
        passed: Whether every readiness check passed.
        reason: Redacted failure reason, when not passed.
    """

    passed: bool
    reason: str | None = None


def validate_broker_readiness(*, evidence: BrokerReadinessEvidence) -> None:
    """Validate broker connection, trading allowance, and rate capacity.

    Args:
        evidence: Broker readiness evidence.

    Raises:
        TradingValidationError: If any readiness dimension fails.
    """
    logger.info("Validating broker readiness evidence.")
    if not evidence.connected:
        raise TradingValidationError("Broker adapter is not connected.")
    if not evidence.trade_allowed:
        raise TradingValidationError("Broker trading is not currently allowed.")
    if not evidence.account_permissions_ok:
        raise TradingValidationError("Account lacks required trading permissions.")
    if not evidence.rate_limit_available:
        raise TradingValidationError("Client-side rate-limit capacity is exhausted.")
    logger.debug("Broker readiness evidence passed.")


def validate_clock_drift(*, evidence: ClockDriftEvidence) -> None:
    """Validate local clock drift and optional PTP end-to-end latency.

    Args:
        evidence: Clock synchronization and PTP latency evidence.

    Raises:
        TradingMappedError: If the clock offset exceeds the configured
            threshold, or PTP end-to-end latency exceeds its threshold.
    """
    logger.info("Validating clock drift, offset_ms={}.", evidence.offset_ms)
    if abs(evidence.offset_ms) > CLOCK_DRIFT_THRESHOLD_MS:
        raise TradingMappedError(
            "Local clock drift exceeds the configured threshold.",
            code="CLOCK_DRIFT_DETECTED",
            details={
                "offset_ms": str(evidence.offset_ms),
                "threshold_ms": str(CLOCK_DRIFT_THRESHOLD_MS),
            },
        )
    if evidence.ptp_aligned and evidence.ptp_latency_ms is not None:
        if evidence.max_ptp_latency_ms is not None:
            if evidence.ptp_latency_ms > evidence.max_ptp_latency_ms:
                raise TradingMappedError(
                    "PTP end-to-end latency exceeds the configured threshold.",
                    code="CLOCK_DRIFT_DETECTED",
                    details={
                        "ptp_latency_ms": str(evidence.ptp_latency_ms),
                        "max_ptp_latency_ms": str(evidence.max_ptp_latency_ms),
                    },
                )
    logger.debug("Clock drift evidence passed.")


def run_live_readiness_dry_run(
    *,
    broker_evidence: BrokerReadinessEvidence,
    clock_evidence: ClockDriftEvidence,
    symbol_metadata_present: bool,
    stores_durable: bool,
) -> ReadinessCheckResult:
    """Run a non-mutating live readiness dry run (TRD-FR-096).

    Verifies broker connection, account identity/permissions, symbol
    metadata availability, clock drift, and store durability without
    dispatching any mock orders.

    Args:
        broker_evidence: Broker readiness evidence.
        clock_evidence: Clock synchronization and PTP latency evidence.
        symbol_metadata_present: Whether symbol metadata is available.
        stores_durable: Whether persistence stores are reachable/durable.

    Returns:
        ReadinessCheckResult: Aggregate dry-run outcome.
    """
    logger.info("Running live readiness dry run.")
    try:
        validate_broker_readiness(evidence=broker_evidence)
        validate_clock_drift(evidence=clock_evidence)
        if not symbol_metadata_present:
            raise TradingValidationError("Symbol metadata is unavailable.")
        if not stores_durable:
            raise TradingValidationError(
                "Persistence stores are not durable or reachable."
            )
    except (TradingValidationError, TradingMappedError) as exc:
        logger.warning("Live readiness dry run failed: {}.", exc)
        return ReadinessCheckResult(passed=False, reason=str(exc))
    logger.debug("Live readiness dry run passed.")
    return ReadinessCheckResult(passed=True)
