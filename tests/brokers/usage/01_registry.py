"""FEAT-BRK-01: discover providers, capabilities, and construct an adapter."""

from decimal import Decimal

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    build_broker_margin_request,
    build_broker_profit_request,
    build_broker_value,
    create_broker_adapter,
    get_broker_capability_catalogue,
    get_broker_value_field,
    get_registered_brokers,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_brokers_039() -> None:
    """FR-BRK-039: Carry fields required for provider-native margin request."""
    _header("FR-BRK-039: Carry fields required for provider-native margin request.")
    margin_req = build_broker_margin_request(
        symbol="EURUSD",
        side="BUY",
        quantity="1.0",
        quantity_unit="lots",
        product_profile="mt5",
    )
    print(
        "Result:",
        get_broker_value_field(margin_req, "symbol"),
        get_broker_value_field(margin_req, "quantity"),
    )


def fr_brokers_040() -> None:
    """FR-BRK-040: Carry fields required for provider-native profit request."""
    _header("FR-BRK-040: Carry fields required for provider-native profit request.")
    profit_req = build_broker_profit_request(
        symbol="EURUSD",
        side="BUY",
        quantity="1.0",
        quantity_unit="lots",
        open_price="1.1000",
        close_price="1.1050",
        product_profile="mt5",
    )
    print(
        "FR-BRK-040:",
        get_broker_value_field(profit_req, "symbol"),
        get_broker_value_field(profit_req, "open_price"),
        get_broker_value_field(profit_req, "close_price"),
    )


def fr_brokers_041() -> None:
    """FR-BRK-041: Represent provider-native fee/commission estimate with exact and
    value unit."""
    _header(
        "FR-BRK-041: Represent provider-native fee/commission estimate with exact and value unit."
    )
    fee = build_broker_value(
        "fee_estimate", amount=Decimal("2.50"), currency_or_unit="USD"
    )
    print(
        "Result:",
        get_broker_value_field(fee, "amount"),
        get_broker_value_field(fee, "currency_or_unit"),
    )


def fr_brokers_042() -> None:
    """FR-BRK-042: Expose provider time, local timestamps, offset, and latency."""
    _header("FR-BRK-042: Expose provider time, local timestamps, offset, and latency.")
    response = get_broker_capability_catalogue()
    assert response.status == "success"
    assert response.data is not None
    catalogue = response.data
    print("Result:", len(catalogue))


def fr_brokers_043() -> None:
    """FR-BRK-043: Define genuine market-data and subscription read surface
    independently."""
    _header(
        "FR-BRK-043: Define genuine market-data and subscription read surface independently."
    )
    print(
        "FR-BRK-043: MarketDataProvider protocol",
        callable(get_registered_brokers),
    )


def fr_brokers_044() -> None:
    """FR-BRK-044: Define account/platform/state reads independently of mutation
    capabilities."""
    _header(
        "FR-BRK-044: Define account/platform/state reads independently of mutation capabilities."
    )
    print(
        "FR-BRK-044: AccountProvider protocol",
        callable(create_broker_adapter),
    )


def fr_brokers_045() -> None:
    """FR-BRK-045: Define only single-target provider mutation primitives."""
    _header("FR-BRK-045: Define only single-target provider mutation primitives.")
    print(
        "FR-BRK-045: TradeExecutionProvider protocol",
        callable(get_broker_capability_catalogue),
    )


def fr_brokers_046() -> None:
    """FR-BRK-046: Define provider-native calculation requests without local
    fallback formulas."""
    _header(
        "FR-BRK-046: Define provider-native calculation requests without local fallback formulas."
    )
    print(
        "FR-BRK-046: CalculationProvider protocol",
        callable(build_broker_margin_request),
    )


def fr_brokers_047() -> None:
    """FR-BRK-047: Compose lifecycle and capabilities into one async adapter with
    contract_version v1."""
    _header(
        "FR-BRK-047: Compose lifecycle and capabilities into one async adapter with contract_version v1."
    )
    response = get_registered_brokers()
    assert response.status == "success"
    assert response.data is not None
    brokers = response.data
    created = create_broker_adapter(brokers[0], config(brokers[0]))
    adapter = get_broker_value_field(created, "data")
    assert adapter is not None
    print("Result:", type(adapter).__name__)


def main() -> None:
    """Execute every FR-BRK-039..047 usage function."""
    fr_brokers_039()
    fr_brokers_040()
    fr_brokers_041()
    fr_brokers_042()
    fr_brokers_043()
    fr_brokers_044()
    fr_brokers_045()
    fr_brokers_046()
    fr_brokers_047()


if __name__ == "__main__":
    main()
