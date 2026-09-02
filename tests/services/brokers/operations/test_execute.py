"""Unit tests for FR 9: Execution Bridge and BrokerOperationsService."""

from __future__ import annotations

from app.services.brokers.operations.execute import (
    BrokerOperationsService,
    connect,
    disconnect,
    fr_brk_operations,
    get_account_info,
    get_orders,
    get_positions,
    get_quote,
    get_symbols,
    is_connected,
    place_order,
)


def test_execution_bridge_functions() -> None:
    """Verify that execute module successfully bridges and exposes all operational functions."""
    connect()
    assert is_connected() is True
    acc = get_account_info()
    assert acc["currency"] == "USD"

    symbols = get_symbols()
    assert len(symbols) >= 4

    quote = get_quote("EURUSD")
    assert quote["bid"] > 0

    orders = get_orders()
    assert len(orders) >= 2

    positions = get_positions()
    assert len(positions) >= 2

    order_res = place_order({"symbol": "EURUSD", "volume": 0.1, "type": "BUY"})
    assert order_res["retcode"] == 0

    report = fr_brk_operations()
    assert report["connected"] is True
    assert report["symbols"] >= 4

    disconnect()


def test_broker_operations_service_methods() -> None:
    """Verify BrokerOperationsService implements BrokerOperationsCapability protocol."""
    service = BrokerOperationsService()
    conn_res = service.connect(10001, "DemoServer")
    assert conn_res["connected"] is True
    assert service.is_connected() is True

    acc = service.get_account_info()
    assert acc["account_id"] == 10001

    sym_info = service.get_symbol_info("EURUSD")
    assert sym_info["symbol"] == "EURUSD"

    quote = service.get_quote("EURUSD")
    assert quote["bid"] > 0

    orders = service.get_orders()
    assert isinstance(orders, list)

    positions = service.get_positions()
    assert isinstance(positions, list)

    order_res = service.place_order({"symbol": "EURUSD", "volume": 0.1, "type": "BUY"})
    assert order_res["retcode"] == 0

    assert service.disconnect() is True
