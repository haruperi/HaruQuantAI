"""Unit tests for evidence/market_context.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.services.data.contracts.responses import build_data_response, data_start_time
from app.services.data.evidence.market_context import get_market_context_evidence
from app.services.data.evidence.market_context_contracts import MarketContextRequest

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)
_MKT_OP = "data.evidence.market_context_provider.get_market_context"


def _wrap(evidence: object) -> object:
    """Wrap raw provider evidence in a successful StandardResponse."""
    return build_data_response(
        operation=_MKT_OP,
        request_id=_REQ_ID,
        start_time=data_start_time(),
        data=evidence,
    )


def test_market_context_provider_exception() -> None:
    """Test get_market_context_evidence surfaces a non-success response when provider raises Exception."""
    mock_provider = MagicMock()
    mock_provider.get_market_context.side_effect = RuntimeError("Provider crashed")

    req = MarketContextRequest(
        symbol="EURUSD",
        timezone="UTC",
        as_of=_NOW,
        max_age_seconds=10,
        requested_evidence=("session",),
        request_id=_REQ_ID,
    )
    response = get_market_context_evidence(req, mock_provider)
    assert response.status != "success"
    assert response.error is not None


def test_market_context_validation_failed() -> None:
    """Test get_market_context_evidence surfaces VALIDATION_FAILED on symbol mismatch or empty provenance."""
    mock_provider = MagicMock()
    mock_evidence = MagicMock()
    mock_evidence.symbol = "WRONG_SYMBOL"
    mock_provider.get_market_context.return_value = _wrap(mock_evidence)

    req = MarketContextRequest(
        symbol="EURUSD",
        timezone="UTC",
        as_of=_NOW,
        max_age_seconds=10,
        requested_evidence=("session",),
        request_id=_REQ_ID,
    )
    response = get_market_context_evidence(req, mock_provider)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "VALIDATION_FAILED"


def test_market_context_stale_evidence() -> None:
    """Test get_market_context_evidence surfaces STALE_EVIDENCE when age > max_age_seconds."""
    mock_provider = MagicMock()
    mock_evidence = MagicMock()
    mock_evidence.symbol = "EURUSD"
    mock_evidence.timezone = "UTC"
    mock_evidence.request_id = _REQ_ID
    mock_evidence.provenance = {"source": "test"}
    mock_evidence.as_of = _NOW - timedelta(
        seconds=100
    )  # Stale: age is 100s, max is 10s
    mock_evidence.expires_at = _NOW + timedelta(seconds=100)
    mock_provider.get_market_context.return_value = _wrap(mock_evidence)

    req = MarketContextRequest(
        symbol="EURUSD",
        timezone="UTC",
        as_of=_NOW,
        max_age_seconds=10,
        requested_evidence=("session",),
        request_id=_REQ_ID,
    )
    response = get_market_context_evidence(req, mock_provider)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "STALE_EVIDENCE"
