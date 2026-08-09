from app.services.indicators import measure_order_flow


def test_order_flow_reports_pressure_and_gap_without_invention() -> None:
    result = measure_order_flow(
        bid_depth=0.0,
        ask_depth=0.0,
        previous_bid_depth=5.0,
        previous_ask_depth=5.0,
        aggressive_buy_volume=9.0,
        aggressive_sell_volume=1.0,
        sweep_threshold=0.7,
    )
    assert result.data["liquidity_gap"] is True
    assert result.data["sweep"] == "BUY"


def test_order_flow_covers_sell_none_and_invalid_states() -> None:
    sell = measure_order_flow(
        bid_depth=1.0,
        ask_depth=2.0,
        previous_bid_depth=1.0,
        previous_ask_depth=2.0,
        aggressive_buy_volume=0.0,
        aggressive_sell_volume=10.0,
        sweep_threshold=0.5,
    )
    none = measure_order_flow(
        bid_depth=1.0,
        ask_depth=1.0,
        previous_bid_depth=1.0,
        previous_ask_depth=1.0,
        aggressive_buy_volume=0.0,
        aggressive_sell_volume=0.0,
        sweep_threshold=0.5,
    )
    invalid = measure_order_flow(
        bid_depth=-1.0,
        ask_depth=1.0,
        previous_bid_depth=1.0,
        previous_ask_depth=1.0,
        aggressive_buy_volume=1.0,
        aggressive_sell_volume=1.0,
        sweep_threshold=0.5,
    )
    assert sell.data["sweep"] == "SELL"
    assert none.data["sweep"] == "NONE"
    assert invalid.status == "error"
