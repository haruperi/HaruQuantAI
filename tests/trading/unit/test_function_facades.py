"""Unit evidence for the Trading package-root function facade."""

from app.services.trading import (
    create_execution_receipt,
    create_trading_error,
    create_trading_request,
    get_trading_contract_version,
    get_trading_route,
    is_execution_receipt,
    is_trading_error,
)

from tests.trading.conftest import authority_receipt, trading_request


def test_contract_facade_constructs_and_inspects_internal_values() -> None:
    """Factories expose validated behavior without exporting implementation classes."""
    request = trading_request()
    rebuilt = create_trading_request(**request.model_dump(mode="python"))
    receipt = authority_receipt()
    rebuilt_receipt = create_execution_receipt(**receipt.model_dump(mode="python"))
    error = create_trading_error("INVALID_REQUEST", "bounded test detail")

    assert rebuilt.request_id == request.request_id
    assert rebuilt_receipt.receipt_id == receipt.receipt_id
    assert get_trading_contract_version() == "v1"
    assert get_trading_route("SIM").value == "sim"
    assert is_execution_receipt(rebuilt_receipt)
    assert is_trading_error(error)
    assert not is_execution_receipt(error)
    assert not is_trading_error(rebuilt_receipt)
