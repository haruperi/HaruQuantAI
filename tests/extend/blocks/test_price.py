"""Unit tests for discrete price building blocks, containers, and Price facade.

Description:
    Tests StrategyQuant donor-faithful price blocks for single-bar OHLCV,
    bid/ask quotes, multi-timeframe daily/weekly/monthly aggregation, session
    windows, Heiken Ashi smoothing, unified Price/Prices facade, and registry
    discovery.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-OPEN: Bar open price tests.
    - FR-PRICE-HIGH: Bar high price tests.
    - FR-PRICE-LOW: Bar low price tests.
    - FR-PRICE-CLOSE: Bar close price tests.
    - FR-PRICE-VOLUME: Bar volume tests.
    - FR-PRICE-ASK: Quote ask price tests.
    - FR-PRICE-BID: Quote bid price tests.
    - FR-PRICE-SPREAD: Quote spread tests.
    - FR-PRICE-SPREAD-IN-PIPS: Pip-scaled spread tests.
    - FR-PRICE-OPEN-D: Daily open tests.
    - FR-PRICE-HIGH-D: Daily high tests.
    - FR-PRICE-LOW-D: Daily low tests.
    - FR-PRICE-CLOSE-D: Daily close tests.
    - FR-PRICE-OPEN-W: Weekly open tests.
    - FR-PRICE-HIGH-W: Weekly high tests.
    - FR-PRICE-LOW-W: Weekly low tests.
    - FR-PRICE-CLOSE-W: Weekly close tests.
    - FR-PRICE-OPEN-M: Monthly open tests.
    - FR-PRICE-HIGH-M: Monthly high tests.
    - FR-PRICE-LOW-M: Monthly low tests.
    - FR-PRICE-CLOSE-M: Monthly close tests.
    - FR-PRICE-HEIKEN-ASHI-OPEN: Heiken Ashi open tests.
    - FR-PRICE-HEIKEN-ASHI-HIGH: Heiken Ashi high tests.
    - FR-PRICE-HEIKEN-ASHI-LOW: Heiken Ashi low tests.
    - FR-PRICE-HEIKEN-ASHI-CLOSE: Heiken Ashi close tests.
    - FR-PRICE-SESSION-OPEN: Session open tests.
    - FR-PRICE-SESSION-HIGH: Session high tests.
    - FR-PRICE-SESSION-LOW: Session low tests.
    - FR-PRICE-SESSION-CLOSE: Session close tests.
    - FR-PRICE-SESSION-CALCULATOR: Session calculator tests.
    - FR-PRICE-FACADE: Price and Prices facade tests.
    - FR-PRICE-EXPORTS: Package aliases and registry discovery tests.
Python API Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
CLI Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest
from app.extend.blocks.price import (
    CLOSE,
    DEFAULT_PIP_SIZE,
    HIGH,
    LOW,
    OPEN,
    Ask,
    BarPrice,
    Bid,
    Close,
    CloseD,
    CloseM,
    CloseW,
    HeikenAshiClose,
    HeikenAshiHigh,
    HeikenAshiLow,
    HeikenAshiOpen,
    High,
    HighD,
    HighM,
    HighW,
    Low,
    LowD,
    LowM,
    LowW,
    MTFPrice,
    Open,
    OpenD,
    OpenM,
    OpenW,
    Price,
    Prices,
    QuotePrice,
    SessionClose,
    SessionHigh,
    SessionLow,
    SessionOHLCCalculator,
    SessionOpen,
    SessionPrice,
    Spread,
    SpreadInPips,
    Volume,
    ask,
    ask_spec,
    bar_close,
    bar_high,
    bar_low,
    bar_open,
    bar_volume,
    bid,
    bid_spec,
    close_d,
    close_d_spec,
    close_m,
    close_m_spec,
    close_spec,
    close_w,
    close_w_spec,
    heiken_ashi_close,
    heiken_ashi_close_spec,
    heiken_ashi_high,
    heiken_ashi_high_spec,
    heiken_ashi_low,
    heiken_ashi_low_spec,
    heiken_ashi_open,
    heiken_ashi_open_spec,
    high_d,
    high_d_spec,
    high_m,
    high_m_spec,
    high_spec,
    high_w,
    high_w_spec,
    low_d,
    low_d_spec,
    low_m,
    low_m_spec,
    low_price,
    low_spec,
    low_w,
    low_w_spec,
    open_d,
    open_d_spec,
    open_m,
    open_m_spec,
    open_price,
    open_spec,
    open_w,
    open_w_spec,
    session_close,
    session_close_spec,
    session_high,
    session_high_spec,
    session_low,
    session_low_spec,
    session_open,
    session_open_spec,
    spread,
    spread_in_pips,
    spread_in_pips_spec,
    spread_spec,
    volume_spec,
)
from app.extend.blocks.registry import BlockRegistry


def test_donor_class_aliases() -> None:
    """Verify all 29 donor class aliases match the blocks and Prices is Price."""
    assert Ask is ask
    assert Bid is bid
    assert Close is bar_close
    assert CloseD is close_d
    assert CloseM is close_m
    assert CloseW is close_w
    assert HeikenAshiClose is heiken_ashi_close
    assert HeikenAshiHigh is heiken_ashi_high
    assert HeikenAshiLow is heiken_ashi_low
    assert HeikenAshiOpen is heiken_ashi_open
    assert High is bar_high
    assert HighD is high_d
    assert HighM is high_m
    assert HighW is high_w
    assert Low is bar_low
    assert LowD is low_d
    assert LowM is low_m
    assert LowW is low_w
    assert Open is bar_open
    assert OpenD is open_d
    assert OpenM is open_m
    assert OpenW is open_w
    assert SessionClose is session_close
    assert SessionHigh is session_high
    assert SessionLow is session_low
    assert SessionOpen is session_open
    assert Spread is spread
    assert SpreadInPips is spread_in_pips
    assert Volume is bar_volume
    assert Prices is Price


def test_bar_price_container() -> None:
    """Verify BarPrice initialization, shifting, series export, and validations."""
    opens = [100.0, 101.0, 102.0]
    highs = [105.0, 106.0, 107.0]
    lows = [95.0, 96.0, 97.0]
    closes = [104.0, 103.0, 105.0]
    vols = [1000.0, 1500.0, 2000.0]

    bp = BarPrice(opens, highs, lows, closes, vols)
    assert len(bp) == 3

    # Shift 0 is latest bar (index 2)
    assert bp.open(0) == 102.0
    assert bp.high(0) == 107.0
    assert bp.low(0) == 97.0
    assert bp.close(0) == 105.0
    assert bp.volume(0) == 2000.0

    # Shift 1 is 1 bar ago (index 1)
    assert bp.open(1) == 101.0
    assert bp.high(1) == 106.0
    assert bp.low(1) == 96.0
    assert bp.close(1) == 103.0
    assert bp.volume(1) == 1500.0

    # Out of bounds
    assert math.isnan(bp.open(3))
    assert math.isnan(bp.close(-1))

    # Read-only views
    assert len(bp.open_values) == 3
    assert len(bp.high_values) == 3
    assert len(bp.low_values) == 3
    assert len(bp.close_values) == 3
    assert len(bp.volume_values) == 3

    # Series exports
    assert bp.open_series().name == "Open"
    assert bp.high_series().name == "High"
    assert bp.low_series().name == "Low"
    assert bp.close_series().name == "Close"
    assert bp.volume_series().name == "Volume"

    # Validation errors
    with pytest.raises(ValueError):
        BarPrice([], [], [], [])
    with pytest.raises(ValueError):
        BarPrice([1.0], [2.0, 3.0], [1.0], [2.0])


def test_quote_price_container() -> None:
    """Verify QuotePrice bid/ask, spread, spread_in_pips, and series exports."""
    bids = [1.1000, 1.1010, 1.1020]
    asks = [1.1002, 1.1013, 1.1024]

    qp = QuotePrice(bids, asks, pip_size=0.0001)
    assert len(qp) == 3
    assert qp.pip_size == DEFAULT_PIP_SIZE

    # Shift 0 is newest
    assert math.isclose(qp.bid(0), 1.1020)
    assert math.isclose(qp.ask(0), 1.1024)
    assert math.isclose(qp.spread(0), 0.0004)
    assert math.isclose(qp.spread_in_pips(0), 4.0)

    # Shift 1
    assert math.isclose(qp.spread(1), 0.0003)
    assert math.isclose(qp.spread_in_pips(1), 3.0)

    # Series
    assert qp.bid_series().name == "Bid"
    assert qp.ask_series().name == "Ask"
    assert qp.spread_series().name == "Spread"
    assert qp.spread_in_pips_series().name == "SpreadInPips"

    # Validation errors
    with pytest.raises(ValueError):
        QuotePrice([], [])
    with pytest.raises(ValueError):
        QuotePrice([1.0], [1.0, 2.0])
    with pytest.raises(ValueError):
        QuotePrice([1.0], [1.0], pip_size=-1)


def test_mtf_price_aggregates() -> None:
    """Verify MTFPrice aggregation into daily, weekly, and monthly bars."""
    t1 = int(datetime(2024, 1, 5, 10, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 5, 14, 0, tzinfo=UTC).timestamp())
    t3 = int(datetime(2024, 1, 8, 10, 0, tzinfo=UTC).timestamp())
    t4 = int(datetime(2024, 1, 9, 10, 0, tzinfo=UTC).timestamp())

    ts = [t1, t2, t3, t4]
    opens = [10.0, 12.0, 20.0, 30.0]
    highs = [15.0, 16.0, 25.0, 35.0]
    lows = [8.0, 11.0, 18.0, 28.0]
    closes = [12.0, 14.0, 22.0, 32.0]

    mtf = MTFPrice(ts, opens, highs, lows, closes)

    # Shift 0 is Day 3
    assert mtf.daily_open(0) == 30.0
    assert mtf.daily_high(0) == 35.0
    assert mtf.daily_low(0) == 28.0
    assert mtf.daily_close(0) == 32.0

    # Shift 2 is Day 1 (merged t1 and t2)
    assert mtf.daily_open(2) == 10.0
    assert mtf.daily_high(2) == 16.0
    assert mtf.daily_low(2) == 8.0
    assert mtf.daily_close(2) == 14.0

    # Weeks
    assert mtf.weekly_open(0) == 20.0
    assert mtf.weekly_high(0) == 35.0
    assert mtf.weekly_low(0) == 18.0
    assert mtf.weekly_close(0) == 32.0

    assert mtf.weekly_open(1) == 10.0
    assert mtf.weekly_close(1) == 14.0

    # Monthly
    assert mtf.monthly_open(0) == 10.0
    assert mtf.monthly_close(0) == 32.0


def test_session_price_and_calculator() -> None:
    """Verify SessionPrice windowing and SessionOHLCCalculator evaluations."""
    t1 = int(datetime(2024, 1, 5, 8, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 5, 9, 0, tzinfo=UTC).timestamp())
    t3 = int(datetime(2024, 1, 5, 12, 0, tzinfo=UTC).timestamp())
    t4 = int(datetime(2024, 1, 5, 16, 0, tzinfo=UTC).timestamp())

    ts = [t1, t2, t3, t4]
    opens = [10.0, 20.0, 30.0, 40.0]
    highs = [12.0, 25.0, 35.0, 42.0]
    lows = [9.0, 18.0, 28.0, 38.0]
    closes = [11.0, 22.0, 32.0, 41.0]

    sp = SessionPrice(
        ts,
        opens,
        highs,
        lows,
        closes,
        start_hour=8,
        start_minute=30,
        end_hour=15,
        end_minute=0,
    )

    assert sp.open(0) == 20.0
    assert sp.high(0) == 35.0
    assert sp.low(0) == 18.0
    assert sp.close(0) == 32.0

    # Test SessionOHLCCalculator
    calc_open = SessionOHLCCalculator(output_type=OPEN, chart=sp)
    assert calc_open.get() == 20.0

    calc_high = SessionOHLCCalculator(output_type=HIGH, chart=sp)
    assert calc_high.get() == 35.0

    calc_low = SessionOHLCCalculator(output_type=LOW, chart=sp)
    assert calc_low.get() == 18.0

    calc_close = SessionOHLCCalculator(output_type=CLOSE, chart=sp)
    assert calc_close.get() == 32.0


def test_discrete_bar_blocks(caplog: pytest.LogCaptureFixture) -> None:
    """Verify bar_open, bar_high, bar_low, bar_close, bar_volume discrete blocks."""
    bp = BarPrice([10.0, 20.0], [15.0, 25.0], [5.0, 15.0], [12.0, 22.0], [100.0, 200.0])

    with caplog.at_level("DEBUG"):
        assert bar_open(bp, 0) == 20.0
        assert open_price(bp, 1) == 10.0
        assert bar_high(bp, 0) == 25.0
        assert bar_low(bp, 0) == 15.0
        assert low_price(bp, 1) == 5.0
        assert bar_close(bp, 0) == 22.0
        assert bar_volume(bp, 0) == 200.0

    assert any("FR-PRICE-OPEN" in r.message for r in caplog.records)
    assert any("FR-PRICE-HIGH" in r.message for r in caplog.records)
    assert any("FR-PRICE-LOW" in r.message for r in caplog.records)
    assert any("FR-PRICE-CLOSE" in r.message for r in caplog.records)
    assert any("FR-PRICE-VOLUME" in r.message for r in caplog.records)


def test_discrete_quote_blocks(caplog: pytest.LogCaptureFixture) -> None:
    """Verify ask, bid, spread, spread_in_pips blocks."""
    qp = QuotePrice([1.2000, 1.2010], [1.2002, 1.2014], pip_size=0.0001)

    with caplog.at_level("DEBUG"):
        assert math.isclose(ask(qp, 0), 1.2014)
        assert math.isclose(bid(qp, 0), 1.2010)
        assert math.isclose(spread(qp, 0), 0.0004)
        assert math.isclose(spread_in_pips(qp, 0), 4.0)

    assert any("FR-PRICE-ASK" in r.message for r in caplog.records)
    assert any("FR-PRICE-BID" in r.message for r in caplog.records)
    assert any("FR-PRICE-SPREAD" in r.message for r in caplog.records)
    assert any("FR-PRICE-SPREAD-IN-PIPS" in r.message for r in caplog.records)


def test_discrete_mtf_blocks(caplog: pytest.LogCaptureFixture) -> None:
    """Verify open_d, high_d, low_d, close_d, and W/M blocks."""
    t1 = int(datetime(2024, 1, 5, 10, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 8, 10, 0, tzinfo=UTC).timestamp())
    mtf = MTFPrice([t1, t2], [10.0, 20.0], [15.0, 25.0], [8.0, 18.0], [12.0, 22.0])

    with caplog.at_level("DEBUG"):
        assert open_d(mtf, 0) == 20.0
        assert high_d(mtf, 0) == 25.0
        assert low_d(mtf, 0) == 18.0
        assert close_d(mtf, 0) == 22.0

        assert open_w(mtf, 0) == 20.0
        assert high_w(mtf, 0) == 25.0
        assert low_w(mtf, 0) == 18.0
        assert close_w(mtf, 0) == 22.0

        assert open_m(mtf, 0) == 10.0
        assert high_m(mtf, 0) == 25.0
        assert low_m(mtf, 0) == 8.0
        assert close_m(mtf, 0) == 22.0

    assert any("FR-PRICE-OPEN-D" in r.message for r in caplog.records)
    assert any("FR-PRICE-CLOSE-W" in r.message for r in caplog.records)
    assert any("FR-PRICE-HIGH-M" in r.message for r in caplog.records)


def test_discrete_session_blocks(caplog: pytest.LogCaptureFixture) -> None:
    """Verify session_open, session_high, session_low, session_close blocks."""
    t1 = int(datetime(2024, 1, 5, 9, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 5, 12, 0, tzinfo=UTC).timestamp())
    sp = SessionPrice([t1, t2], [10.0, 20.0], [15.0, 25.0], [8.0, 18.0], [12.0, 22.0])

    with caplog.at_level("DEBUG"):
        assert session_open(sp, shift=0) == 10.0
        assert session_high(sp, shift=0) == 25.0
        assert session_low(sp, shift=0) == 8.0
        assert session_close(sp, shift=0) == 22.0

    assert any("FR-PRICE-SESSION-OPEN" in r.message for r in caplog.records)
    assert any("FR-PRICE-SESSION-HIGH" in r.message for r in caplog.records)
    assert any("FR-PRICE-SESSION-LOW" in r.message for r in caplog.records)
    assert any("FR-PRICE-SESSION-CLOSE" in r.message for r in caplog.records)


def test_heiken_ashi_blocks(caplog: pytest.LogCaptureFixture) -> None:
    """Verify heiken_ashi_open, heiken_ashi_high, heiken_ashi_low, heiken_ashi_close."""
    bp = BarPrice([10.0, 20.0], [15.0, 25.0], [8.0, 18.0], [12.0, 22.0])

    with caplog.at_level("DEBUG"):
        # Shift 0 is Bar 1
        assert heiken_ashi_close(bp, 0) == 21.25
        assert heiken_ashi_open(bp, 0) == 11.125
        assert heiken_ashi_high(bp, 0) == 25.0
        assert heiken_ashi_low(bp, 0) == 11.125

        # Shift 1 is Bar 0
        assert heiken_ashi_close(bp, 1) == 11.25
        assert heiken_ashi_open(bp, 1) == 11.0
        assert heiken_ashi_high(bp, 1) == 15.0
        assert heiken_ashi_low(bp, 1) == 8.0

    assert any("FR-PRICE-HEIKEN-ASHI-CLOSE" in r.message for r in caplog.records)
    assert any("FR-PRICE-HEIKEN-ASHI-OPEN" in r.message for r in caplog.records)


def test_price_facade(caplog: pytest.LogCaptureFixture) -> None:
    """Verify Price facade methods routing."""
    bp = BarPrice([10.0, 20.0], [15.0, 25.0], [8.0, 18.0], [12.0, 22.0], [100.0, 200.0])

    with caplog.at_level("DEBUG"):
        assert Price.open(bp, 0) == 20.0
        assert Price.high(bp, 0) == 25.0
        assert Price.low(bp, 0) == 18.0
        assert Price.close(bp, 0) == 22.0
        assert Price.volume(bp, 0) == 200.0
        assert Prices.close(bp, 0) == 22.0

    assert any("FR-PRICE-FACADE" in r.message for r in caplog.records)


def test_all_29_price_block_specs() -> None:
    """Verify all 29 price block specifications are valid."""
    specs = [
        open_spec,
        high_spec,
        low_spec,
        close_spec,
        volume_spec,
        ask_spec,
        bid_spec,
        spread_spec,
        spread_in_pips_spec,
        open_d_spec,
        high_d_spec,
        low_d_spec,
        close_d_spec,
        open_w_spec,
        high_w_spec,
        low_w_spec,
        close_w_spec,
        open_m_spec,
        high_m_spec,
        low_m_spec,
        close_m_spec,
        session_open_spec,
        session_high_spec,
        session_low_spec,
        session_close_spec,
        heiken_ashi_open_spec,
        heiken_ashi_high_spec,
        heiken_ashi_low_spec,
        heiken_ashi_close_spec,
    ]
    assert len(specs) == 29
    for s in specs:
        assert s.id.startswith("price.")
        assert s.category == "price"
        assert len(s.inputs) >= 1
        assert len(s.outputs) == 1
        assert s.is_causal is True


def test_block_registry_discovers_all_price_blocks() -> None:
    """Verify BlockRegistry discovers all 29 price blocks with 0 diagnostics."""
    registry = BlockRegistry()
    registry.discover("app/extend/blocks/price")

    expected_ids = {
        "price.ask",
        "price.bid",
        "price.close",
        "price.close_d",
        "price.close_m",
        "price.close_w",
        "price.heiken_ashi_close",
        "price.heiken_ashi_high",
        "price.heiken_ashi_low",
        "price.heiken_ashi_open",
        "price.high",
        "price.high_d",
        "price.high_m",
        "price.high_w",
        "price.low",
        "price.low_d",
        "price.low_m",
        "price.low_w",
        "price.open",
        "price.open_d",
        "price.open_m",
        "price.open_w",
        "price.session_close",
        "price.session_high",
        "price.session_low",
        "price.session_open",
        "price.spread",
        "price.spread_in_pips",
        "price.volume",
    }
    discovered = {b.spec.id for b in registry.snapshot().blocks.values()}
    assert expected_ids.issubset(discovered)
    assert not registry.diagnostics
