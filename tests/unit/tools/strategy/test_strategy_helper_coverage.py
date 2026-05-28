"""Focused coverage tests for strategy helper modules."""

from __future__ import annotations

import pandas as pd
import pytest

from tools.strategy.base import StatefulEventStrategy, VectorizedSignalStrategy
from tools.strategy.contracts import PositionSnapshot, StrategyContext
from tools.strategy.examples.trade_decomposition import TradeDecompositionStrategy
from tools.strategy.stateful_helpers import (
    basket_pnl,
    current_mid_price,
    historical_mid_prices,
    oldest_position,
    positions_for_side,
    rolling_rsi,
    rolling_sma,
    weighted_average_price,
)
from tools.strategy.storage import StrategyStorage
from tools.utils.validators import (
    assert_dataframe,
    assert_ohlc_dataframe,
    ensure_no_signal_columns,
    ensure_signal_columns,
    normalize_signal_columns,
    serialize_dataframe,
    validate_strategy_dataframe,
    validate_trade_action_object,
    validate_trade_actions,
)


class DemoVectorStrategy(VectorizedSignalStrategy):
    """Concrete strategy used to exercise BaseStrategy helpers."""

    def on_init(self) -> None:
        """Initialize test state."""
        self.state["ready"] = True

    def on_bar(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return prepared signal output."""
        return self.prepare_output(data)


class DemoStatefulStrategy(StatefulEventStrategy):
    """Concrete stateful strategy used to exercise base defaults."""

    def on_init(self) -> None:
        """Initialize test state."""
        self.state["ready"] = True


def _context(
    *,
    prices: list[float] | None = None,
    positions: list[PositionSnapshot] | None = None,
    bid: float = 1.1050,
    ask: float = 1.1052,
) -> StrategyContext:
    values = (
        [1.1000 + index * 0.0001 for index in range(40)] if prices is None else prices
    )
    data = pd.DataFrame({"bid": values, "ask": [price + 0.0001 for price in values]})
    return StrategyContext(
        strategy_id="helper-test",
        symbol="EURUSD",
        market_data=data,
        current_tick={"bid": bid, "ask": ask, "is_bar_close": "close"},
        positions=positions or [],
        metadata={"tick_index": len(data) - 1},
    )


def test_base_strategy_hooks_and_signal_helpers(ohlc_data: pd.DataFrame) -> None:
    strategy = DemoVectorStrategy({"symbol": "EURUSD", "strategy_id": "demo"})
    strategy.on_init()
    prepared = strategy.on_bar(ohlc_data)
    first_index = prepared.index[0]
    prepared.loc[first_index, "entry_signal"] = 1
    prepared.loc[first_index, "price"] = pd.NA
    prepared.loc[first_index, "stop_loss"] = 0.99
    prepared.loc[first_index, "take_profit"] = 1.05
    prepared.loc[first_index, "setup_id"] = "setup-1"

    signal = strategy.get_signal(prepared, 0)

    assert signal is not None
    assert signal["price"] == prepared.loc[first_index, "close"]
    assert strategy.get_signal(prepared, 1) is None
    assert strategy.crossover(pd.Series([1, 3]), pd.Series([2, 2])) is True
    assert strategy.crossunder(pd.Series([3, 1]), pd.Series([2, 2])) is True
    assert strategy.crossover(pd.Series([1]), pd.Series([1])) is False
    assert strategy.crossunder(pd.Series([1]), pd.Series([1])) is False
    assert strategy.on_tick(ohlc_data).equals(ohlc_data)
    assert strategy.on_trade({}) is None
    assert strategy.on_order_update({}) is None
    assert strategy.on_timer({}) is None
    assert strategy.on_shutdown() is None

    with pytest.raises(ValueError):
        strategy.get_signal("bad", 0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        strategy.get_signal(prepared, -1)


def test_stateful_strategy_base_and_helpers() -> None:
    stateful = DemoStatefulStrategy({"symbol": "EURUSD"})
    data = pd.DataFrame({"open": [1.0], "high": [1.1], "low": [0.9], "close": [1.0]})
    buy = PositionSnapshot(
        ticket="1",
        symbol="EURUSD",
        side="BUY",
        volume=0.2,
        open_price=1.1000,
        opened_at="2026-01-01T00:00:00Z",
        profit_loss=5.0,
    )
    sell = PositionSnapshot(
        ticket="2",
        symbol="EURUSD",
        side="SELL",
        volume=0.1,
        open_price=1.2000,
        opened_at="2026-01-02T00:00:00Z",
        profit_loss=-1.0,
    )
    context = _context(positions=[buy, sell])

    assert "entry_signal" in stateful.on_bar(data).columns
    assert stateful.on_event(context) == []
    assert current_mid_price(context) == pytest.approx(1.1051)
    assert current_mid_price(_context(bid=0.0, ask=1.2)) == 1.2
    assert current_mid_price(_context(bid=1.1, ask=0.0)) == 1.1
    assert len(historical_mid_prices(context)) == 40
    empty_context = _context(prices=[])
    empty_context.market_data = pd.DataFrame()
    assert historical_mid_prices(empty_context).empty
    assert positions_for_side(context, "BUY") == [buy]
    assert basket_pnl([buy, sell]) == 4.0
    assert weighted_average_price([buy, sell]) == pytest.approx(1.1333333333)
    assert weighted_average_price([]) is None
    assert oldest_position([sell, buy]) == buy
    assert oldest_position([]) is None
    assert rolling_sma(pd.Series([1.0, 2.0, 3.0]), 2) == 2.5
    assert rolling_sma(pd.Series([1.0]), 2) is None
    assert rolling_rsi(pd.Series([1, 2, 3, 4, 5], dtype=float), 3) == 100.0
    assert rolling_rsi(pd.Series([1.0, 2.0]), 3) is None

    with pytest.raises(ValueError):
        positions_for_side(context, "HOLD")
    with pytest.raises(ValueError):
        rolling_sma(pd.Series([1.0]), 0)
    with pytest.raises(ValueError):
        rolling_rsi(pd.Series([1.0]), 0)


def test_validation_helpers_and_error_branches(ohlc_data: pd.DataFrame) -> None:
    normalized = ensure_signal_columns(ohlc_data, include_activators=True)
    neutral = ensure_no_signal_columns(normalized)
    serialized = serialize_dataframe(neutral.head(1))

    assert "buy_setup_active" in normalized.columns
    assert neutral["entry_signal"].eq(0).all()
    assert serialized["rows"][0]["entry_signal"] == 0
    assert validate_strategy_dataframe(ohlc_data, min_rows=10)["status"] == "success"
    assert normalize_signal_columns(ohlc_data)["status"] == "success"
    assert validate_trade_actions("bad")["status"] == "error"  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        assert_dataframe("bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        assert_dataframe(pd.DataFrame(), min_rows=1)
    with pytest.raises(ValueError):
        assert_ohlc_dataframe(ohlc_data.drop(columns=["open"]))
    with pytest.raises(ValueError):
        validate_trade_action_object({"action_type": "BAD", "symbol": "EURUSD"})
    with pytest.raises(ValueError):
        validate_trade_action_object({"action_type": "OPEN", "symbol": ""})
    with pytest.raises(ValueError):
        validate_trade_action_object({"action_type": "OPEN", "symbol": "EURUSD"})
    with pytest.raises(ValueError):
        validate_trade_action_object(
            {"action_type": "CLOSE", "symbol": "EURUSD", "side": "BUY", "volume": 1}
        )


def test_storage_versions_and_overwrite(tmp_path) -> None:
    storage = StrategyStorage(tmp_path)
    record = storage.save_strategy_source(
        strategy_name="demo",
        version="1.0.0",
        source_code="class Demo: pass\n",
    )

    assert record.strategy_name == "demo"
    assert storage.list_strategy_versions("demo") == ["1.0.0"]
    assert storage.list_strategy_versions("missing") == []

    with pytest.raises(FileExistsError):
        storage.save_strategy_source(
            strategy_name="demo",
            version="1.0.0",
            source_code="class Demo: pass\n",
        )

    overwritten = storage.save_strategy_source(
        strategy_name="demo",
        version="1.0.0",
        source_code="class Demo2: pass\n",
        overwrite=True,
    )
    assert overwritten.path == record.path

    with pytest.raises(ValueError):
        storage.save_strategy_source(
            strategy_name="demo",
            version="1.0.1",
            source_code=" ",
        )
    with pytest.raises(ValueError):
        storage.list_strategy_versions("../bad")


def test_trade_decomposition_branches() -> None:
    strategy = TradeDecompositionStrategy(
        {
            "symbol": "EURUSD",
            "rsi_period": 3,
            "trade_distance": 1,
            "child_take_profit_pips": 1,
        }
    )
    strategy.on_init()
    parent = PositionSnapshot(
        ticket="parent",
        symbol="EURUSD",
        side="BUY",
        volume=0.2,
        open_price=1.1000,
        opened_at="2026-01-01T00:00:00Z",
        setup_id="basket-1",
    )
    child = PositionSnapshot(
        ticket="child",
        symbol="EURUSD",
        side="BUY",
        volume=0.1,
        open_price=1.0990,
        opened_at="2026-01-02T00:00:00Z",
        metadata={"role": "child"},
    )

    strategy.state["previous_rsi"] = 20.0
    no_bar_close = _context(positions=[], ask=1.1010)
    no_bar_close.current_tick["is_bar_close"] = "tick"
    assert strategy.on_event(no_bar_close) == []

    strategy.state["previous_rsi"] = 80.0
    context = _context(positions=[parent, child], bid=1.1015, ask=1.1016)
    actions = strategy.on_event(context)
    assert {action.action_type for action in actions} >= {"CLOSE", "MOVE_TO_BREAKEVEN"}

    strategy.state["previous_rsi"] = 10.0
    sell_context = _context(
        positions=[
            PositionSnapshot(
                ticket="sell-parent",
                symbol="EURUSD",
                side="SELL",
                volume=0.2,
                open_price=1.1000,
            )
        ],
        bid=1.1020,
        ask=1.1021,
    )
    sell_actions = strategy.on_event(sell_context)
    assert any(action.action_type == "REDUCE" for action in sell_actions)
