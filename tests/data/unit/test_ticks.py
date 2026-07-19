"""Unit tests for real-evidence tick-series generation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts.errors import DataError
from app.services.data.contracts.market import DataQualityReport, MarketDataset
from app.services.data.contracts.records import OHLCVRecord, TickRecord
from app.services.data.processing.ticks import (
    GENERATED_TICKS_MIN_PER_BAR,
    PHASE_CLOSE,
    PHASE_HIGH,
    PHASE_LOW,
    PHASE_OPEN,
    generate_tick_series,
)

_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _quality(count: int) -> DataQualityReport:
    return DataQualityReport(
        quality_status="passed",
        quality_score=Decimal("1.0"),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=_START,
    )


def _bar(
    index: int,
    open_value: str,
    high: str,
    low: str,
    close: str,
    volume: str = "10",
    spread: str | None = "2",
) -> OHLCVRecord:
    timestamp = _START + timedelta(minutes=index)
    return OHLCVRecord(
        timestamp=timestamp,
        source="test",
        source_symbol="EURUSD",
        source_revision="v1",
        available_at=timestamp,
        open=Decimal(open_value),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        price_unit="price",
        volume_unit="ticks",
        spread=None if spread is None else Decimal(spread),
        spread_unit=None if spread is None else "points",
    )


def _bar_dataset(records: tuple[OHLCVRecord, ...]) -> MarketDataset:
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=_quality(len(records)),
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-d3b07384-d113-4404-94c5-000000000001",
    )


def _bullish_dataset() -> MarketDataset:
    return _bar_dataset((_bar(0, "1.10000", "1.10200", "1.09900", "1.10100"),))


def test_trading_bar_model_emits_four_direction_ordered_waypoints() -> None:
    """A bullish bar visits open, low, high, then close."""
    result = generate_tick_series(
        _bullish_dataset(),
        model="trading_bar",
        trading_timeframe="M1",
    )

    assert result.data_kind == "ticks"
    assert result.record_count == 4
    bids = [record.bid for record in result.records if isinstance(record, TickRecord)]
    assert bids == [
        Decimal("1.10000"),
        Decimal("1.09900"),
        Decimal("1.10200"),
        Decimal("1.10100"),
    ]


def test_bearish_bar_visits_high_before_low() -> None:
    """A bearish bar reverses the intra-bar extreme ordering."""
    dataset = _bar_dataset((_bar(0, "1.10100", "1.10200", "1.09900", "1.10000"),))

    result = generate_tick_series(dataset, model="trading_bar", trading_timeframe="M1")

    bids = [record.bid for record in result.records if isinstance(record, TickRecord)]
    assert bids[1] == Decimal("1.10200")
    assert bids[2] == Decimal("1.09900")


def test_phase_bitmask_marks_open_high_low_close() -> None:
    """Every canonical waypoint carries its phase bit."""
    result = generate_tick_series(
        _bullish_dataset(), model="trading_bar", trading_timeframe="M1"
    )

    phases = [
        record.bar_phase for record in result.records if isinstance(record, TickRecord)
    ]
    assert phases == [PHASE_OPEN, PHASE_LOW, PHASE_HIGH, PHASE_CLOSE]


def test_generated_model_uses_real_tick_volume() -> None:
    """Generated tick count equals the real tick volume of the bar."""
    dataset = _bar_dataset(
        (_bar(0, "1.10000", "1.10200", "1.09900", "1.10100", volume="7"),)
    )

    result = generate_tick_series(dataset, model="generated", trading_timeframe="M1")

    assert result.record_count == 7


def test_generated_model_clamps_to_minimum_waypoints() -> None:
    """A bar with fewer real ticks than waypoints still emits all four."""
    dataset = _bar_dataset(
        (_bar(0, "1.10000", "1.10200", "1.09900", "1.10100", volume="1"),)
    )

    result = generate_tick_series(dataset, model="generated", trading_timeframe="M1")

    assert result.record_count == GENERATED_TICKS_MIN_PER_BAR


def test_generated_prices_stay_within_real_bar_bounds() -> None:
    """Interpolation never leaves the real high/low envelope."""
    dataset = _bar_dataset(
        (_bar(0, "1.10000", "1.10200", "1.09900", "1.10100", volume="25"),)
    )

    result = generate_tick_series(dataset, model="generated", trading_timeframe="M1")

    for record in result.records:
        assert isinstance(record, TickRecord)
        assert record.bid is not None
        assert Decimal("1.09900") <= record.bid <= Decimal("1.10200")


def test_generate_tick_series_preserves_real_prices_and_volume() -> None:
    """Open and close of every bar survive unchanged into the tick stream."""
    dataset = _bar_dataset(
        (
            _bar(0, "1.10000", "1.10200", "1.09900", "1.10100"),
            _bar(1, "1.10100", "1.10300", "1.10000", "1.10250"),
        )
    )

    result = generate_tick_series(dataset, model="trading_bar", trading_timeframe="M1")

    ticks = [r for r in result.records if isinstance(r, TickRecord)]
    assert ticks[0].bid == Decimal("1.10000")
    assert ticks[3].bid == Decimal("1.10100")
    assert ticks[4].bid == Decimal("1.10100")
    assert ticks[7].bid == Decimal("1.10250")


def test_output_is_ordered_by_timestamp_then_intrabar_index() -> None:
    """Ordering is total and reproducible."""
    dataset = _bar_dataset(
        (
            _bar(0, "1.10000", "1.10200", "1.09900", "1.10100"),
            _bar(1, "1.10100", "1.10300", "1.10000", "1.10250"),
        )
    )

    result = generate_tick_series(dataset, model="trading_bar", trading_timeframe="M1")

    keys = [
        (r.timestamp, r.tick_index_in_bar)
        for r in result.records
        if isinstance(r, TickRecord)
    ]
    assert keys == sorted(keys)


def test_native_spread_produces_ask_above_bid() -> None:
    """Native spread evidence is applied in price units."""
    result = generate_tick_series(
        _bullish_dataset(),
        model="trading_bar",
        trading_timeframe="M1",
        point_value=Decimal("0.00001"),
    )

    first = next(r for r in result.records if isinstance(r, TickRecord))
    assert first.ask is not None
    assert first.bid is not None
    assert first.ask - first.bid == Decimal("0.00002")


def test_fixed_spread_requires_points() -> None:
    """A fixed spread model without its point value fails closed."""
    with pytest.raises(DataError):
        generate_tick_series(
            _bullish_dataset(),
            model="trading_bar",
            trading_timeframe="M1",
            spread_model="fixed_spread",
        )


def test_variable_spread_requires_seed_and_replays() -> None:
    """Variable spread needs a seed and reproduces identical output."""
    dataset = _bar_dataset(
        (_bar(0, "1.10000", "1.10200", "1.09900", "1.10100", volume="12"),)
    )
    arguments = {
        "model": "generated",
        "trading_timeframe": "M1",
        "spread_model": "variable_spread",
        "min_spread_points": Decimal(1),
        "max_spread_points": Decimal(5),
    }

    with pytest.raises(DataError):
        generate_tick_series(dataset, **arguments)  # type: ignore[arg-type]

    kwargs = {"seed": 99, **arguments}
    first = generate_tick_series(dataset, **kwargs)  # type: ignore[arg-type]
    second = generate_tick_series(dataset, **kwargs)  # type: ignore[arg-type]

    assert [r.ask for r in first.records] == [r.ask for r in second.records]


def test_unsupported_model_fails_closed() -> None:
    """An unrecognized model is rejected rather than falling back."""
    with pytest.raises(DataError):
        generate_tick_series(
            _bullish_dataset(),
            model="not_a_model",
            trading_timeframe="M1",
        )


def test_record_count_ceiling_is_enforced() -> None:
    """Exceeding the configured output bound raises rather than truncating."""
    dataset = _bar_dataset(
        (_bar(0, "1.10000", "1.10200", "1.09900", "1.10100", volume="500"),)
    )

    with pytest.raises(DataError):
        generate_tick_series(
            dataset,
            model="generated",
            trading_timeframe="M1",
            max_records=10,
        )


def test_generated_ticks_carry_no_strategy_fields() -> None:
    """Data records expose no signal, order, or protective-level concept."""
    result = generate_tick_series(
        _bullish_dataset(), model="trading_bar", trading_timeframe="M1"
    )

    forbidden = {
        "entry_signal",
        "exit_signal",
        "pending_signal",
        "cancel_pending_signal",
        "sl",
        "tp",
    }
    for record in result.records:
        assert not forbidden & set(type(record).model_fields)


def test_source_metadata_records_generation_provenance() -> None:
    """Model, spread model, and seed are recorded on the dataset."""
    result = generate_tick_series(
        _bullish_dataset(), model="trading_bar", trading_timeframe="M1"
    )

    assert result.source_metadata["tick_generation_model"] == "trading_bar"
    assert result.source_metadata["tick_spread_model"] == "native_spread"
    assert result.source_metadata["tick_generation_seed"] == "none"


def test_bars_required_for_bar_derived_models() -> None:
    """A tick dataset cannot feed a bar-derived model."""
    tick = TickRecord(
        timestamp=_START,
        source="test",
        source_symbol="EURUSD",
        available_at=_START,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        price_unit="price",
    )
    dataset = MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        records=(tick,),
        start=_START,
        end=_START,
        available_at=_START,
        record_count=1,
        quality_report=_quality(1),
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-d3b07384-d113-4404-94c5-000000000002",
    )

    with pytest.raises(DataError):
        generate_tick_series(dataset, model="trading_bar", trading_timeframe="M1")


def test_ohlc_m1_model_requires_m1_dataset() -> None:
    """The M1 model fails closed without its finer-grained evidence."""
    with pytest.raises(DataError):
        generate_tick_series(
            _bullish_dataset(), model="ohlc_m1", trading_timeframe="M5"
        )


def test_real_model_marks_bucket_extremes() -> None:
    """Real ticks receive open, high, low, and close phase evidence."""
    ticks = tuple(
        TickRecord(
            timestamp=_START + timedelta(seconds=index * 10),
            source="test",
            source_symbol="EURUSD",
            available_at=_START + timedelta(seconds=index * 10),
            bid=Decimal(price),
            ask=Decimal(price) + Decimal("0.00002"),
            price_unit="price",
        )
        for index, price in enumerate(["1.10000", "1.10050", "1.09950", "1.10020"])
    )
    tick_dataset = MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        records=ticks,
        start=ticks[0].timestamp,
        end=ticks[-1].timestamp,
        available_at=ticks[-1].available_at,
        record_count=len(ticks),
        quality_report=_quality(len(ticks)),
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-d3b07384-d113-4404-94c5-000000000003",
    )

    result = generate_tick_series(
        _bullish_dataset(),
        model="real",
        trading_timeframe="M1",
        real_tick_dataset=tick_dataset,
    )

    phases = [r.bar_phase for r in result.records if isinstance(r, TickRecord)]
    assert phases[0] is not None
    assert phases[0] & PHASE_OPEN
    assert phases[-1] is not None
    assert phases[-1] & PHASE_CLOSE
    assert any(phase is not None and phase & PHASE_HIGH for phase in phases)
    assert any(phase is not None and phase & PHASE_LOW for phase in phases)
