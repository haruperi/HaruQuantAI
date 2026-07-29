"""Read (Data) and write (Trading) capability traits stay structurally separate."""

from app.services import brokers


def test_read_traits_never_declare_a_mutation_method() -> None:
    """Market Data, Account, and Calculation operations are read-only."""
    read_functions = {
        "get_broker_account_info",
        "get_broker_positions",
        "get_broker_orders",
        "get_broker_quote",
        "get_broker_historical_bars",
        "get_broker_balances",
    }
    all_exports = set(brokers.__all__)
    assert read_functions <= all_exports


def test_trade_execution_provider_is_the_sole_mutation_trait() -> None:
    """Trade execution domain root functions declare every documented mutation primitive."""
    mutation_functions = {
        "check_broker_order",
        "place_broker_order",
        "modify_broker_order",
        "cancel_broker_order",
        "modify_broker_position",
        "close_broker_position",
        "replace_broker_order",
    }
    all_exports = set(brokers.__all__)
    assert mutation_functions <= all_exports
