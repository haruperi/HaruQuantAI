"""Unit tests for broker readiness and clock synchronization gate primitives."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.gates.readiness import (
    BrokerReadinessEvidence,
    ClockDriftEvidence,
    run_live_readiness_dry_run,
    validate_broker_readiness,
    validate_clock_drift,
)
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingValidationError,
)


def _broker(**overrides: object) -> BrokerReadinessEvidence:
    defaults: dict[str, object] = {
        "connected": True,
        "trade_allowed": True,
        "account_permissions_ok": True,
        "rate_limit_available": True,
    }
    defaults.update(overrides)
    return BrokerReadinessEvidence(**defaults)  # type: ignore[arg-type]


def test_validate_broker_readiness_rejects_not_connected() -> None:
    """A disconnected broker adapter fails closed."""
    with pytest.raises(TradingValidationError, match="connected"):
        validate_broker_readiness(evidence=_broker(connected=False))


def test_validate_broker_readiness_rejects_trade_not_allowed() -> None:
    """Trading not allowed fails closed."""
    with pytest.raises(TradingValidationError, match="allowed"):
        validate_broker_readiness(evidence=_broker(trade_allowed=False))


def test_validate_broker_readiness_rejects_missing_permissions() -> None:
    """Missing account permissions fails closed."""
    with pytest.raises(TradingValidationError, match="permissions"):
        validate_broker_readiness(evidence=_broker(account_permissions_ok=False))


def test_validate_broker_readiness_rejects_rate_limit_exhausted() -> None:
    """Exhausted client-side rate limit capacity fails closed."""
    with pytest.raises(TradingValidationError, match="rate-limit"):
        validate_broker_readiness(evidence=_broker(rate_limit_available=False))


def test_validate_broker_readiness_passes_when_fully_ready() -> None:
    """Fully ready evidence passes without raising."""
    validate_broker_readiness(evidence=_broker())


def test_validate_clock_drift_rejects_excess_offset() -> None:
    """An offset beyond the threshold fails closed."""
    with pytest.raises(TradingMappedError) as exc_info:
        validate_clock_drift(evidence=ClockDriftEvidence(offset_ms=Decimal(75)))
    assert exc_info.value.code == "CLOCK_DRIFT_DETECTED"


def test_validate_clock_drift_passes_without_ptp_alignment() -> None:
    """A within-threshold offset with no PTP alignment passes."""
    validate_clock_drift(
        evidence=ClockDriftEvidence(offset_ms=Decimal(10), ptp_aligned=False)
    )


def test_validate_clock_drift_passes_when_ptp_latency_absent() -> None:
    """PTP alignment without a measured latency skips the PTP check."""
    validate_clock_drift(
        evidence=ClockDriftEvidence(
            offset_ms=Decimal(10), ptp_aligned=True, ptp_latency_ms=None
        )
    )


def test_validate_clock_drift_passes_when_max_latency_unconfigured() -> None:
    """PTP latency measured but no threshold configured skips the check."""
    validate_clock_drift(
        evidence=ClockDriftEvidence(
            offset_ms=Decimal(10),
            ptp_aligned=True,
            ptp_latency_ms=Decimal(5),
            max_ptp_latency_ms=None,
        )
    )


def test_validate_clock_drift_passes_within_ptp_latency_threshold() -> None:
    """PTP latency within the configured threshold passes."""
    validate_clock_drift(
        evidence=ClockDriftEvidence(
            offset_ms=Decimal(10),
            ptp_aligned=True,
            ptp_latency_ms=Decimal(5),
            max_ptp_latency_ms=Decimal(10),
        )
    )


def test_validate_clock_drift_rejects_excess_ptp_latency() -> None:
    """PTP latency beyond the configured threshold fails closed."""
    with pytest.raises(TradingMappedError) as exc_info:
        validate_clock_drift(
            evidence=ClockDriftEvidence(
                offset_ms=Decimal(10),
                ptp_aligned=True,
                ptp_latency_ms=Decimal(20),
                max_ptp_latency_ms=Decimal(10),
            )
        )
    assert exc_info.value.code == "CLOCK_DRIFT_DETECTED"


def test_run_live_readiness_dry_run_fails_on_broker_readiness() -> None:
    """The dry run reports failure when broker readiness fails."""
    result = run_live_readiness_dry_run(
        broker_evidence=_broker(connected=False),
        clock_evidence=ClockDriftEvidence(offset_ms=Decimal(0)),
        symbol_metadata_present=True,
        stores_durable=True,
    )
    assert result.passed is False
    assert result.reason is not None


def test_run_live_readiness_dry_run_fails_on_missing_symbol_metadata() -> None:
    """The dry run reports failure when symbol metadata is unavailable."""
    result = run_live_readiness_dry_run(
        broker_evidence=_broker(),
        clock_evidence=ClockDriftEvidence(offset_ms=Decimal(0)),
        symbol_metadata_present=False,
        stores_durable=True,
    )
    assert result.passed is False


def test_run_live_readiness_dry_run_fails_on_store_durability() -> None:
    """The dry run reports failure when stores are not durable."""
    result = run_live_readiness_dry_run(
        broker_evidence=_broker(),
        clock_evidence=ClockDriftEvidence(offset_ms=Decimal(0)),
        symbol_metadata_present=True,
        stores_durable=False,
    )
    assert result.passed is False


def test_run_live_readiness_dry_run_passes_when_fully_ready() -> None:
    """The dry run passes when every dimension is ready."""
    result = run_live_readiness_dry_run(
        broker_evidence=_broker(),
        clock_evidence=ClockDriftEvidence(offset_ms=Decimal(0)),
        symbol_metadata_present=True,
        stores_durable=True,
    )
    assert result.passed is True
    assert result.reason is None
