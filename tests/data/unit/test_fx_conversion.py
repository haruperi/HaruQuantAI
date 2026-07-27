"""Unit tests for FX conversion evidence service."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from app.services.data.contracts import DataError
from app.services.data.evidence.fx_contracts import (
    FXConversionRequest,
    FXRateLeg,
)
from app.services.data.evidence.fx_conversion import (
    get_fx_conversion_evidence,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def _make_leg(
    source: str = "EUR",
    target: str = "USD",
    rate: Decimal = Decimal("1.0850"),
    as_of: datetime = _NOW,
    source_id: str = "mt5",
    provenance: dict[str, str] | None = None,
) -> FXRateLeg:
    return FXRateLeg(
        source_currency=source,
        target_currency=target,
        rate=rate,
        as_of=as_of,
        source_id=source_id,
        provider_symbol=f"{source}{target}",
        provenance=provenance or {"broker": "mt5"},
    )


def _make_req(
    source: str = "EUR",
    target: str = "USD",
    max_legs: int = 2,
    intermediates: tuple[str, ...] = ("GBP", "CHF"),
) -> FXConversionRequest:
    return FXConversionRequest(
        source_currency=source,
        target_currency=target,
        as_of=_NOW,
        max_age_seconds=60,
        max_legs=max_legs,
        allowed_intermediates=intermediates,
        path_policy_id="policy-1",
        path_policy_version="v1",
        request_id=_REQ_ID,
    )


def test_fx_conversion_direct_success() -> None:
    """Test successful direct FX conversion."""
    provider = MagicMock()
    provider.get_rate_leg.return_value = _make_leg()
    req = _make_req()

    evidence = get_fx_conversion_evidence(req, provider)
    assert evidence.source_currency == "EUR"
    assert evidence.target_currency == "USD"
    assert evidence.composite_rate == Decimal("1.0850")
    assert evidence.provenance["selection"] == "direct"


def test_fx_conversion_two_leg_synthetic_success() -> None:
    """Test successful 2-leg synthetic FX conversion."""
    provider = MagicMock()
    leg1 = _make_leg("EUR", "GBP", Decimal("0.8500"))
    leg2 = _make_leg("GBP", "JPY", Decimal("190.00"))

    def mock_get_leg(*, source_currency, target_currency, **_kwargs):
        if source_currency == "EUR" and target_currency == "JPY":
            raise DataError("DATA_NOT_FOUND", request_id=_REQ_ID)
        if source_currency == "EUR" and target_currency == "GBP":
            return leg1
        if source_currency == "GBP" and target_currency == "JPY":
            return leg2
        raise DataError("DATA_NOT_FOUND", request_id=_REQ_ID)

    provider.get_rate_leg.side_effect = mock_get_leg
    req = _make_req("EUR", "JPY", max_legs=2, intermediates=("GBP",))

    evidence = get_fx_conversion_evidence(req, provider)
    assert evidence.composite_rate == Decimal("0.8500") * Decimal("190.00")
    assert evidence.provenance["selection"] == "declared_intermediate"


def test_fx_conversion_stale_evidence_raises() -> None:
    """Test stale rate leg raises STALE_EVIDENCE DataError."""
    provider = MagicMock()
    stale_as_of = _NOW - timedelta(seconds=120)
    provider.get_rate_leg.return_value = _make_leg(as_of=stale_as_of)
    req = _make_req()

    with pytest.raises(DataError) as exc_info:
        get_fx_conversion_evidence(req, provider)
    assert exc_info.value.code == "STALE_EVIDENCE"


def test_fx_conversion_validation_failed_raises() -> None:
    """Test mismatched leg attributes raise VALIDATION_FAILED DataError."""
    provider = MagicMock()
    invalid_leg = _make_leg("GBP", "USD")  # Requested EUR/USD, returned GBP/USD
    provider.get_rate_leg.return_value = invalid_leg
    req = _make_req()

    with pytest.raises(DataError) as exc_info:
        get_fx_conversion_evidence(req, provider)
    assert exc_info.value.code == "VALIDATION_FAILED"


def test_fx_conversion_provider_unhandled_exception_raises() -> None:
    """Test unexpected provider exception raises SOURCE_UNAVAILABLE DataError."""
    provider = MagicMock()
    provider.get_rate_leg.side_effect = RuntimeError("Provider offline")
    req = _make_req()

    with pytest.raises(DataError) as exc_info:
        get_fx_conversion_evidence(req, provider)
    assert exc_info.value.code == "SOURCE_UNAVAILABLE"


def test_fx_conversion_max_legs_exceeded_raises() -> None:
    """Test max_legs restriction when direct fails."""
    provider = MagicMock()
    provider.get_rate_leg.side_effect = DataError("DATA_NOT_FOUND", request_id=_REQ_ID)
    req = _make_req(max_legs=1)

    with pytest.raises(DataError) as exc_info:
        get_fx_conversion_evidence(req, provider)
    assert exc_info.value.code == "DATA_NOT_FOUND"
