from typing import Any

from tests.unit.app.services.analytics.compat_test_helper import (
    adjusted_net_profit_as_percent_of_max_trade_drawdown,
    net_profit_as_percent_of_max_trade_drawdown,
    runs_test_zscore,
    select_gross_loss,
    select_gross_profit,
    select_net_profit,
    select_net_profit_as_percent_of_max_trade_drawdown,
    win_after_win_probability,
)
from tests.unit.app.services.analytics.compat_test_helper import (
    rolling_expectancy_stability as expectancy_std,
)


def make_trade(
    pnl: float, is_open: bool = False, close_time: str = "2026-01-01T00:00:00Z"
) -> dict[str, Any]:
    return {"pnl": pnl, "is_open": is_open, "close_time": close_time}


def test_expectancy_std():
    # Less than window
    assert expectancy_std([make_trade(1.0)], window=2) == 0.0

    # Simple cases
    t1 = make_trade(10.0, close_time="2026-01-01T10:00:00Z")
    t2 = make_trade(20.0, close_time="2026-01-01T11:00:00Z")
    t3 = make_trade(30.0, close_time="2026-01-01T12:00:00Z")
    t4 = make_trade(40.0, close_time="2026-01-01T13:00:00Z")

    val = expectancy_std([t1, t2, t3, t4], window=2)
    assert val > 0.0


def test_win_after_win_probability():
    assert win_after_win_probability([make_trade(1.0)]) == 0.0

    t1 = make_trade(10.0, close_time="2026-01-01T10:00:00Z")
    t2 = make_trade(-10.0, close_time="2026-01-01T11:00:00Z")
    t3 = make_trade(10.0, close_time="2026-01-01T12:00:00Z")
    t4 = make_trade(10.0, close_time="2026-01-01T13:00:00Z")

    # Wins at indices 0, 2, 3. Win after win happens only from 2->3.
    # Total wins that have a following trade:
    # t1 (followed by t2=loss), t3 (followed by t4=win).
    # So 1 out of 2.
    assert win_after_win_probability([t1, t2, t3, t4]) == 0.5


def test_runs_test_zscore():
    assert runs_test_zscore([make_trade(1.0)]) == 0.0
    # all positive
    assert runs_test_zscore([make_trade(1.0), make_trade(1.0)]) == 0.0

    t1 = make_trade(10.0, close_time="2026-01-01T10:00:00Z")
    t2 = make_trade(-10.0, close_time="2026-01-01T11:00:00Z")
    t3 = make_trade(10.0, close_time="2026-01-01T12:00:00Z")
    t4 = make_trade(-10.0, close_time="2026-01-01T13:00:00Z")

    z = runs_test_zscore([t1, t2, t3, t4])
    assert z != 0.0


def test_select_profits_and_losses():
    trades = [make_trade(float(i)) for i in range(-50, 50)]
    np = select_net_profit(trades)
    gp = select_gross_profit(trades)
    gl = select_gross_loss(trades)
    assert np != 0.0
    assert gp != 0.0
    assert gl != 0.0

    assert select_net_profit([]) == 0.0
    assert select_gross_profit([]) == 0.0
    assert select_gross_loss([]) == 0.0


def test_profit_drawdown_ratios():
    assert select_net_profit_as_percent_of_max_trade_drawdown(100.0, 50.0) == 200.0
    assert select_net_profit_as_percent_of_max_trade_drawdown(100.0, 0.0) == 0.0

    assert adjusted_net_profit_as_percent_of_max_trade_drawdown(100.0, 50.0) == 200.0
    assert adjusted_net_profit_as_percent_of_max_trade_drawdown(100.0, 0.0) == 0.0

    assert net_profit_as_percent_of_max_trade_drawdown(100.0, 50.0) == 200.0
    assert net_profit_as_percent_of_max_trade_drawdown(100.0, 0.0) == 0.0
