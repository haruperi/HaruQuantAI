"""Behavioral qualification of post-backtest WhatIf scenarios."""

from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

import pytest
from app.include.blocks.strategy_control.history import ClosedTrade
from app.include.what_if import (
    SCENARIOS,
    BaseWhatIf,
    ByDays,
    ByHours,
    ByMonths,
    ExcludeOverlappingTrades,
    ExcludePctTradesWithBiggestPl,
    ExcludePctTradesWithLowestPl,
    ExcludeShortTrades,
    ExcludeTradesWithBiggestPl,
    ExcludeTradesWithLowestPl,
    RemoveBalanceTransactions,
    RemovePendingTrades,
    Swap,
    TakeEverySecondTrade,
    TakeMaxTradesPerDay,
    UseFixedLots,
    WhatIfRecord,
)
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor._template_generators import _gen_what_if
from app.workspace.code_editor.registry import SnippetRegistry
from pydantic import ValidationError


def ms(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=UTC).timestamp() * 1000)


def record(index: int = 1, **kwargs: object) -> WhatIfRecord:
    return WhatIfRecord.model_validate(
        {
            "record_id": index,
            "time_open_msc": ms("2026-10-26T10:00:00"),
            "time_close_msc": ms("2026-10-26T10:05:00"),
        }
        | kwargs
    )


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_empty_and_schema(scenario: type[BaseWhatIf]) -> None:
    instance = scenario()
    assert instance.filter_trades([]) == []
    assert "name" not in scenario.get_parameter_schema().get("properties", {})
    with pytest.raises(ValidationError):
        scenario(unknown=True)


def test_all_scenarios_leave_source_unchanged() -> None:
    source = [record(1, profit=10.0), record(2, profit=-20.0)]
    original = [t.model_dump() for t in source]
    for cls in SCENARIOS:
        result = cls().filter_trades(source)
        assert result is not source
        assert [t.model_dump() for t in source] == original
    with pytest.raises(ValidationError):
        source[0].profit = 42.0


def test_ranking_counts_ties_and_non_trades() -> None:
    source = [
        record(1, profit=20.0),
        record(2, profit=20.0),
        record(3, profit=-10.0),
        record(4, profit=100.0, kind="balance"),
        record(5, profit=-100.0, kind="pending"),
    ]
    assert [
        t.record_id for t in ExcludeTradesWithBiggestPl(trades=1).filter_trades(source)
    ] == [4, 2, 3, 5]
    assert [
        t.record_id for t in ExcludeTradesWithLowestPl(trades=1).filter_trades(source)
    ] == [4, 1, 2, 3]
    assert [
        t.record_id
        for t in ExcludePctTradesWithBiggestPl(trades_pct=1).filter_trades(source)
    ] == [4, 2, 3, 5]
    assert [
        t.record_id
        for t in ExcludePctTradesWithLowestPl(trades_pct=100).filter_trades(source)
    ] == [4, 5]
    assert [
        t.record_id for t in ExcludeTradesWithLowestPl(trades=100).filter_trades(source)
    ] == [4]


def test_calendar_and_timezone() -> None:
    sunday = record(
        time_open_msc=ms("2026-10-25T23:30:00"),
        time_close_msc=ms("2026-10-26T00:00:00"),
    )
    assert ByDays(days=(1,)).filter_trades([sunday]) == []
    assert ByDays(days=(1,), timezone="Europe/Berlin").filter_trades([sunday]) == [
        sunday
    ]
    assert ByHours(hours=(23,)).filter_trades([sunday]) == [sunday]
    assert ByMonths(months=(10,)).filter_trades([sunday]) == [sunday]
    assert ByMonths(months=()).filter_trades([sunday]) == []


def test_alternation_and_daily_limit() -> None:
    source = [
        record(3),
        record(4, kind="balance"),
        record(1),
        record(2, kind="pending"),
        record(5),
    ]
    # Stable sorting preserves incoming order on identical open timestamps.
    assert [t.record_id for t in TakeEverySecondTrade().filter_trades(source)] == [
        3,
        4,
        2,
        5,
    ]
    assert [
        t.record_id for t in TakeMaxTradesPerDay(trades=1).filter_trades(source)
    ] == [3, 4]
    next_day = record(
        6,
        time_open_msc=ms("2026-10-27T10:00:00"),
        time_close_msc=ms("2026-10-27T11:00:00"),
    )
    assert (
        TakeMaxTradesPerDay(trades=1).filter_trades([*source, next_day])[-1] == next_day
    )


def test_overlapping_inclusive_boundary_and_unsorted_input() -> None:
    first = record(1, time_open_msc=0, time_close_msc=10)
    same = record(2, time_open_msc=10, time_close_msc=30)
    after = record(3, time_open_msc=11, time_close_msc=20)
    assert ExcludeOverlappingTrades().filter_trades([after, same, first]) == [
        first,
        after,
    ]


def test_short_duration_is_not_short_direction() -> None:
    source = [
        record(1, kind="balance"),
        record(2, direction=1),
        record(3, direction=-1),
        record(4, time_close_msc=ms("2026-10-26T10:10:00")),
    ]
    # Ceiling uses all input entries, as in the donor.
    assert [
        t.record_id for t in ExcludeShortTrades(trades_pct=25).filter_trades(source)
    ] == [1, 3, 4]
    assert [
        t.record_id for t in ExcludeShortTrades(trades_pct=100).filter_trades(source)
    ] == [1, 4]
    assert RemoveBalanceTransactions().filter_trades(source) == source[1:]
    pending = record(kind="pending")
    assert RemovePendingTrades().filter_trades([pending, source[0]]) == [source[0]]


def test_fixed_lots_costs_and_zero_volume_balance() -> None:
    trade = record(profit=100.0, volume=2.0, commission=-3.0, swap=-2.0, fee=-1.0)
    balance = record(2, kind="balance", volume=0.0, profit=1000.0)
    changed, unchanged = UseFixedLots(size=0.5).filter_trades([trade, balance])
    assert changed.profit == 25.0
    assert changed.volume == 0.5
    assert changed.net_profit == 19.0
    assert unchanged is balance


def test_swap_rollovers_volume_direction_and_boundaries() -> None:
    trade = record(
        time_open_msc=ms("2026-10-27T22:00:00"),
        time_close_msc=ms("2026-10-29T23:00:00"),
        volume=2.0,
        swap=-5.0,
    )
    # Tue=1, Wed=3, Thu=1, includes closing rollover.
    assert Swap().filter_trades([trade])[0].swap == 95.0
    short = WhatIfRecord.model_validate(trade.model_dump() | {"direction": -1})
    assert Swap().filter_trades([short])[0].swap == -105.0
    opened_at_rollover = record(
        time_open_msc=ms("2026-10-28T23:00:00"),
        time_close_msc=ms("2026-10-28T23:00:00"),
    )
    assert Swap().filter_trades([opened_at_rollover])[0].swap == 0
    balance = record(kind="balance", volume=0.0)
    assert Swap().filter_trades([balance]) == [balance]


@pytest.mark.parametrize(
    ("cls", "kwargs"),
    [
        (ByDays, {"days": (0,)}),
        (ByHours, {"hours": (24,)}),
        (ByMonths, {"months": (13,)}),
        (ByDays, {"timezone": "Missing/Zone"}),
        (TakeMaxTradesPerDay, {"trades": True}),
        (ExcludeShortTrades, {"minutes": 0}),
        (UseFixedLots, {"size": float("nan")}),
        (Swap, {"swap_long": float("inf")}),
        (Swap, {"triple_swap_day": 8}),
        (ExcludePctTradesWithLowestPl, {"trades_pct": 0}),
    ],
)
def test_invalid_config(cls: type[BaseWhatIf], kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        cls(**kwargs)


def test_closed_trade_adapter() -> None:
    closed = ClosedTrade(
        1, "EURUSD", 1, 0, "", 1.0, 1.1, 1.2, 0, 1000, 2, 10.0, -1.0, -2.0, -3.0
    )
    adapted = WhatIfRecord.from_closed_trade(closed)
    assert adapted.net_profit == closed.net_profit
    assert adapted.record_id == closed.position_id
    assert adapted.time_close_msc == closed.time_close_msc


def test_template_and_registration() -> None:
    module = ModuleType("test_what_if_extension")
    exec(_gen_what_if("loss_filter"), module.__dict__)
    registry = SnippetRegistry()
    path = Path("app/include/what_if/loss_filter.py")
    assert registry.register(path, module) == ["LossFilter"]
    scenario = module.LossFilter()
    assert scenario.filter_trades([record(profit=-1000.0)]) == []
    invalid = ModuleType("invalid_what_if")
    exec("class Wrong: pass", invalid.__dict__)
    with pytest.raises(CodeEditorError, match="BaseWhatIf"):
        registry.register(path, invalid)
    assert "LossFilter" in registry.blocks[str(path)]


@pytest.mark.parametrize(
    "changes",
    [
        {"volume": 0.0},
        {"direction": 0},
        {"profit": float("nan")},
        {"time_close_msc": -1},
        {"kind": "unknown"},
    ],
)
def test_invalid_analysis_records(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        record(**changes)


def test_swap_uses_local_calendar_across_dst() -> None:
    trade = record(
        time_open_msc=ms("2026-10-24T20:00:00"),
        time_close_msc=ms("2026-10-26T22:00:00"),
    )
    # Berlin's 23:00 rollover changes from 21:00 to 22:00 UTC on Oct 25.
    changed = Swap(timezone="Europe/Berlin").filter_trades([trade])[0]
    assert changed.swap == 30.0


def test_calendar_parameters_round_trip_json() -> None:
    original = ByDays(days=(1, 5), timezone="Africa/Cairo")
    restored = ByDays.model_validate_json(original.model_dump_json())
    assert restored == original
