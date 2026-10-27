"""History selection, record contracts and independent package imports."""

import asyncio
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime

import pandas as pd
import pytest
from app.include.contracts import BridgeError, MarketBar, MarketTick
from app.include.enums import Timeframe
from app.workspace.data_manager.data.conversions import (
    bars_to_dataframe,
    ticks_to_dataframe,
)
from app.workspace.data_manager.data.history import (
    get_historical_bars,
    get_ticks,
    resolve_history_request,
    validate_rows,
)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_history_readers_support_sync_and_async_backends(asynchronous):
    bar = MarketBar(time=1700000000, open=1, high=2, low=0.5, close=1.5)
    tick = MarketTick(time_msc=1700000000123, bid=1.1, ask=1.2)
    calls = []

    async def resolved(value):
        return value

    class Backend:
        def get_bars(self, **kwargs):
            calls.append(kwargs)
            result = [asdict(bar)]
            return resolved(result) if asynchronous else result

        def get_ticks(self, **kwargs):
            calls.append(kwargs)
            result = [asdict(tick)]
            return resolved(result) if asynchronous else result

    backend = Backend()
    start = datetime.fromtimestamp(bar.time, UTC)
    bars = asyncio.run(
        get_historical_bars(backend, "EURUSD", Timeframe.PERIOD_M1, start, start)
    )
    assert bars.Close.tolist() == [1.5]
    assert calls[0]["date_from"] == start
    ticks = asyncio.run(get_ticks(backend, "EURUSD", count=1))
    assert ticks.index[0].microsecond == 123000
    assert ticks.Bid.tolist() == [1.1]
    assert calls[1]["count"] == 1


def test_selectors_and_invalid_chronology():
    date = datetime(2025, 1, 1, tzinfo=UTC)
    assert resolve_history_request(date, None, None, 3, 10, scale=1)[0] == "date_count"
    assert resolve_history_request(None, None, 2, 3, 10, scale=1) == (
        "position",
        2,
        2**63 - 1,
        3,
    )
    with pytest.raises(BridgeError, match="conflicting"):
        resolve_history_request(date, None, 1, None, 10, scale=1)
    row = asdict(MarketBar(time=1700000000, open=1, high=2, low=0.5, close=1.5))
    with pytest.raises(BridgeError, match="chronology"):
        validate_rows([row, row], "bars", row["time"], row["time"] + 60, 10)


def test_conversion_schema_precision_and_empty_frames():
    bar = MarketBar(time=1700000000, open=1, high=2, low=0.5, close=1.5, tick_volume=7)
    frame = bars_to_dataframe([bar])
    assert list(frame.columns) == ["Open", "High", "Low", "Close", "Volume", "Spread"]
    assert frame.Volume.iloc[0] == 7
    assert frame.index.name == "DateTime" and frame.index.tz is None
    assert frame.index[0] == pd.Timestamp("2023-11-14 22:13:20")
    tick = MarketTick(time_msc=1700000000123, bid=1.1, ask=1.2)
    assert ticks_to_dataframe([tick]).index[0].microsecond == 123000
    assert list(bars_to_dataframe([]).columns) == list(frame.columns)
    assert list(ticks_to_dataframe([]).columns) == ["Bid", "Ask"]


@pytest.mark.parametrize("module", ["conversions", "history"])
def test_primitive_import_does_not_initialize_workspace_features(module):
    script = f"""
import importlib
import sys
importlib.import_module('app.workspace.data_manager.data.{module}')
for name in ('app.workspace.data_manager.sources', 'app.workspace.data_manager.data.feature',
             'app.workspace.data_manager.data.http', 'app.host.transport', 'fastapi'):
    assert name not in sys.modules, name
"""
    subprocess.run(
        [sys.executable, "-c", script], check=True, capture_output=True, text=True
    )
