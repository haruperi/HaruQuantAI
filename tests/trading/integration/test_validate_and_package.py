"""Workflow integration for validation and deterministic packaging."""

# ruff: noqa: INP001

import pytest
from app.services.trading.contracts import TradingError
from app.services.trading.validation import (
    ReadinessAssessment,
    build_execution_plan,
    validate_order_request,
)
from tests.trading.conftest import (
    NOW,
    account_snapshot,
    symbol_capability,
    trading_request,
)


def test_validate_and_package_fails_closed() -> None:
    """Invalid instrument evidence blocks before deterministic packaging."""
    item = trading_request(instrument_quantity_step=None)
    capability, _info = symbol_capability(item.route, item.provider_id, item.symbol)
    with pytest.raises(TradingError, match="VALIDATION_FAILED"):
        validate_order_request(item, account_snapshot(), capability)
    valid = trading_request()
    readiness = ReadinessAssessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"data": "snapshot"},
        assessed_at=NOW,
    )
    assert build_execution_plan(valid, readiness).approved_volume == valid.quantity
