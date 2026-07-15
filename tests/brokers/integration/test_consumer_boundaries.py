"""Read (Data) and write (Trading) capability traits stay structurally separate."""

from app.services.brokers import (
    AccountProvider,
    CalculationProvider,
    MarketDataProvider,
    TradeExecutionProvider,
)


def test_read_traits_never_declare_a_mutation_method() -> None:
    """MarketDataProvider/AccountProvider/CalculationProvider expose no writes."""
    mutation_names = {
        "place_order",
        "modify_order",
        "cancel_order",
        "modify_position",
        "close_position",
        "replace_order",
    }
    for protocol in (MarketDataProvider, AccountProvider, CalculationProvider):
        declared = set(dir(protocol))
        assert not mutation_names & declared, protocol


def test_trade_execution_provider_is_the_sole_mutation_trait() -> None:
    """Only TradeExecutionProvider declares every documented mutation primitive."""
    mutation_names = {
        "check_order",
        "place_order",
        "modify_order",
        "cancel_order",
        "modify_position",
        "close_position",
        "replace_order",
    }
    declared = set(dir(TradeExecutionProvider))
    assert mutation_names <= declared
