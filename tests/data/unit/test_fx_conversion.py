"""Unit tests for FX conversion evidence service."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import build_data_response, data_start_time
from app.services.data.evidence.fx_contracts import (
    FXConversionRequest,
    FXRateLeg,
)
from app.services.data.evidence.fx_conversion import (
    get_fx_conversion_evidence,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)
_RATE_LEG_OP = "data.evidence.fx_rate_provider.get_rate_leg"
_FX_OP = "data.evidence.get_fx_conversion_evidence"


def _unwrap(response):
    """Extract the raw payload from a migrated FX conversion response."""
    assert response.status == "success", response.error
    return response.data


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


def _leg_response(leg: FXRateLeg) -> object:
    """Wrap a raw leg in a successful StandardResponse for a fake provider."""
    return build_data_response(
        operation=_RATE_LEG_OP,
        request_id=_REQ_ID,
        start_time=data_start_time(),
        data=leg,
    )


def _leg_error_response(code: str) -> object:
    """Wrap a canonical failure in a StandardResponse for a fake provider."""
    return build_data_response(
        operation=_RATE_LEG_OP,
        request_id=_REQ_ID,
        start_time=data_start_time(),
        error=DataError(code, request_id=_REQ_ID),
    )


def test_fx_conversion_direct_success() -> None:
    """Test successful direct FX conversion."""
    provider = MagicMock()
    provider.get_rate_leg.return_value = _leg_response(_make_leg())
    req = _make_req()

    evidence = _unwrap(get_fx_conversion_evidence(req, provider))
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
            return _leg_error_response("DATA_NOT_FOUND")
        if source_currency == "EUR" and target_currency == "GBP":
            return _leg_response(leg1)
        if source_currency == "GBP" and target_currency == "JPY":
            return _leg_response(leg2)
        return _leg_error_response("DATA_NOT_FOUND")

    provider.get_rate_leg.side_effect = mock_get_leg
    req = _make_req("EUR", "JPY", max_legs=2, intermediates=("GBP",))

    evidence = _unwrap(get_fx_conversion_evidence(req, provider))
    assert evidence.composite_rate == Decimal("0.8500") * Decimal("190.00")
    assert evidence.provenance["selection"] == "declared_intermediate"


def test_fx_conversion_stale_evidence_raises() -> None:
    """Test stale rate leg surfaces STALE_EVIDENCE error response."""
    provider = MagicMock()
    stale_as_of = _NOW - timedelta(seconds=120)
    provider.get_rate_leg.return_value = _leg_response(_make_leg(as_of=stale_as_of))
    req = _make_req()

    response = get_fx_conversion_evidence(req, provider)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "STALE_EVIDENCE"


def test_fx_conversion_validation_failed_raises() -> None:
    """Test mismatched leg attributes surface VALIDATION_FAILED error response."""
    provider = MagicMock()
    invalid_leg = _make_leg("GBP", "USD")  # Requested EUR/USD, returned GBP/USD
    provider.get_rate_leg.return_value = _leg_response(invalid_leg)
    req = _make_req()

    response = get_fx_conversion_evidence(req, provider)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "VALIDATION_FAILED"


def test_fx_conversion_provider_unhandled_exception_raises() -> None:
    """Test unexpected provider exception surfaces a non-success error response."""
    provider = MagicMock()
    provider.get_rate_leg.side_effect = RuntimeError("Provider offline")
    req = _make_req()

    response = get_fx_conversion_evidence(req, provider)
    assert response.status != "success"
    assert response.error is not None


def test_fx_conversion_max_legs_exceeded_raises() -> None:
    """Test max_legs restriction when direct fails."""
    provider = MagicMock()
    provider.get_rate_leg.return_value = _leg_error_response("DATA_NOT_FOUND")
    req = _make_req(max_legs=1)

    response = get_fx_conversion_evidence(req, provider)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "DATA_NOT_FOUND"
