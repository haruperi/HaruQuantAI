"""FEAT-BRK-01: discover providers, capabilities, and construct an adapter."""

from decimal import Decimal

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    AccountProvider,
    BrokerFeeEstimate,
    BrokerMarginRequest,
    BrokerProfitRequest,
    CalculationProvider,
    MarketDataProvider,
    TradeExecutionProvider,
    create_broker_adapter,
    get_broker_capability_catalogue,
    get_registered_brokers,
)


def fr_brokers_039() -> None:
    """FR-BRK-039: Carry fields required for provider-native margin request."""
    margin_req = BrokerMarginRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        product_profile="mt5",
    )
    print("FR-BRK-039:", margin_req.symbol, margin_req.quantity)


def fr_brokers_040() -> None:
    """FR-BRK-040: Carry fields required for provider-native profit request."""
    profit_req = BrokerProfitRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        open_price=Decimal("1.1000"),
        close_price=Decimal("1.1050"),
        product_profile="mt5",
    )
    print(
        "FR-BRK-040:", profit_req.symbol, profit_req.open_price, profit_req.close_price
    )


def fr_brokers_041() -> None:
    """FR-BRK-041: Represent provider-native fee/commission estimate with exact and
    value unit."""
    fee = BrokerFeeEstimate(amount=Decimal("2.50"), currency_or_unit="USD")
    print("FR-BRK-041:", fee.amount, fee.currency_or_unit)


def fr_brokers_042() -> None:
    """FR-BRK-042: Expose provider time, local timestamps, offset, and latency."""
    catalogue = get_broker_capability_catalogue()
    print("FR-BRK-042:", len(catalogue))


def fr_brokers_043() -> None:
    """FR-BRK-043: Define genuine market-data and subscription read surface
    independently."""
    print(
        "FR-BRK-043: MarketDataProvider protocol",
        hasattr(MarketDataProvider, "get_quote"),
    )


def fr_brokers_044() -> None:
    """FR-BRK-044: Define account/platform/state reads independently of mutation
    capabilities."""
    print(
        "FR-BRK-044: AccountProvider protocol",
        hasattr(AccountProvider, "get_account_info"),
    )


def fr_brokers_045() -> None:
    """FR-BRK-045: Define only single-target provider mutation primitives."""
    print(
        "FR-BRK-045: TradeExecutionProvider protocol",
        hasattr(TradeExecutionProvider, "place_order"),
    )


def fr_brokers_046() -> None:
    """FR-BRK-046: Define provider-native calculation requests without local
    fallback formulas."""
    print(
        "FR-BRK-046: CalculationProvider protocol",
        hasattr(CalculationProvider, "calculate_margin"),
    )


def fr_brokers_047() -> None:
    """FR-BRK-047: Compose lifecycle and capabilities into one async adapter with
    contract_version v1."""
    brokers = get_registered_brokers()
    created = create_broker_adapter(brokers[0], config(brokers[0]))
    adapter = created.data
    assert adapter is not None
    print("FR-BRK-047:", adapter.contract_version, adapter.schema_id)


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
