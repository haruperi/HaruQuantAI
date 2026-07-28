"""Workflow integration for validation and deterministic packaging."""

# ruff: noqa: INP001
from app.services.trading import (
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
    invalid = validate_order_request(item, account_snapshot(), capability)
    assert invalid.status == "error"
    assert invalid.error is not None
    assert invalid.error.code == "VALIDATION_FAILED"
    valid = trading_request()
    readiness = ReadinessAssessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"data": "snapshot"},
        assessed_at=NOW,
    )
    result = build_execution_plan(valid, readiness)
    assert result.status == "success"
    assert result.data is not None
    assert result.data.approved_volume == valid.quantity
