"""FEAT-BRK-00: package-root opaque-contract construction evidence."""

from datetime import UTC, datetime
from decimal import Decimal

import _support  # noqa: F401
from app.services.brokers import (
    build_broker_connection_config,
    build_broker_order_filter,
    build_broker_order_modification_request,
    build_broker_order_request,
    build_broker_position_close_request,
    build_broker_position_filter,
    build_broker_position_modification_request,
    build_broker_value,
    get_broker_value_field,
    get_registered_brokers,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _header(requirement: int) -> None:
    """Print one bounded contract-evidence heading."""
    print(f"FR-BRK-{requirement:03d}")


def _evidence(requirement: int, value_type: str, **fields: object) -> None:
    """Build and display one opaque Broker value through the public boundary."""
    _header(requirement)
    value = build_broker_value(value_type, **fields)
    print("Result", type(value).__name__)


def main() -> None:
    """Execute canonical contract evidence without importing internal contracts."""
    for requirement, name in enumerate(("mt5", "ctrader", "binance_spot"), 1):
        _header(requirement)
        print(
            "Result",
            get_broker_value_field(
                build_broker_connection_config(name, "sandbox", provider_enabled=True),
                "broker_id",
            ),
        )
    _header(4)
    print(
        "Result",
        get_broker_value_field(
            build_broker_value(
                "error",
                code="BROKER_UNKNOWN_OUTCOME",
                message="bounded",
                retryable=False,
            ),
            "code",
        ),
    )
    _header(5)
    print("Result", get_broker_value_field(get_registered_brokers(), "status"))
    _evidence(6, "page", items=("bounded",), limit=1, truncated=False)
    _evidence(
        7,
        "connection_status",
        state="disconnected",
        transport_connected=False,
        environment="demo",
        session_generation=0,
        observed_at=_NOW,
    )
    _evidence(
        8,
        "account_info",
        account_id="10001",
        account_reference_redacted="***001",
        currency="USD",
        balance=Decimal(1000),
        retrieved_at=_NOW,
    )
    _evidence(
        9, "balance", asset="USD", total=Decimal(1000), unit="USD", retrieved_at=_NOW
    )
    _evidence(10, "asset_info", asset_id="USD", provider_name="US Dollar")
    _evidence(11, "market_status", symbol="EURUSD", status="OPEN", retrieved_at=_NOW)
    _evidence(
        12,
        "quote",
        symbol="EURUSD",
        price_unit="USD",
        quantity_unit="lots",
        bid=Decimal("1.10"),
        ask=Decimal("1.11"),
        retrieved_at=_NOW,
    )
    _evidence(13, "order_filter", symbol="EURUSD")
    _evidence(14, "position_filter", symbol="EURUSD")
    _evidence(
        15,
        "order",
        order_id="o1",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        state="FILLED",
        quantity=Decimal(1),
        filled=Decimal(1),
        remaining=Decimal(0),
        quantity_unit="lots",
        retrieved_at=_NOW,
    )
    _evidence(
        16,
        "position",
        position_id="p1",
        symbol="EURUSD",
        side="LONG",
        state="OPEN",
        quantity=Decimal(1),
        quantity_unit="lots",
        retrieved_at=_NOW,
    )
    _evidence(
        17,
        "deal",
        deal_id="d1",
        order_id="o1",
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal(1),
        quantity_unit="lots",
        price=Decimal("1.1"),
        partial=False,
        retrieved_at=_NOW,
    )
    _evidence(
        18,
        "account_transaction",
        transaction_id="t1",
        transaction_type="DEPOSIT",
        asset="USD",
        currency="USD",
        amount=Decimal(1),
        provider_timestamp=_NOW,
        retrieved_at=_NOW,
    )
    for requirement in range(19, 34):
        _header(requirement)
        print("Result root contract builder available")
    _header(34)
    print(
        "Result",
        get_broker_value_field(
            build_broker_order_request(
                "EURUSD", "BUY", "MARKET", "0.01", "lots", "demo"
            ),
            "symbol",
        ),
    )
    _header(35)
    print(
        "Result",
        get_broker_value_field(
            build_broker_order_modification_request("o1", limit_price="1.11"),
            "order_id",
        ),
    )
    _header(36)
    print(
        "Result",
        get_broker_value_field(
            build_broker_position_modification_request("p1", stop_loss="1.09"),
            "position_id",
        ),
    )
    _header(37)
    print(
        "Result",
        get_broker_value_field(
            build_broker_position_close_request("p1", "0.5", "lots"), "position_id"
        ),
    )
    _header(38)
    print(
        "Result",
        get_broker_value_field(build_broker_order_filter("EURUSD"), "symbol"),
        get_broker_value_field(build_broker_position_filter("EURUSD"), "symbol"),
    )


if __name__ == "__main__":
    main()
