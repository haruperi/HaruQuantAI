"""Executable usage demonstration harness for Bar Aggregation."""

from __future__ import annotations

import asyncio
from decimal import Decimal

from app.contracts.data.models import (
    AggregateBarsRequest,
    AggregateBarsSuccess,
    AggregationSpec,
    Bar,
    Tick,
)
from app.services.data.bar_aggregation.bar_aggregation import (
    BarAggregationService,
    _format_decimal,
    _generate_uuid7,
    data_aggregate_timeframes,
    data_define_custom_timeframes,
    data_record_aggregation_lineage,
)


def example_resampling(m1_bars: list[Bar] | None = None) -> tuple[Bar, ...]:
    """Resample deterministic M1 bars to closed M5 bars using real market data."""
    bars = m1_bars
    if bars is None:
        from pathlib import Path

        import pandas as pd

        csv_path = Path("data/raw/BTCUSDT_m1.csv")
        if csv_path.exists():
            df = pd.read_csv(csv_path).head(5)
            bars = [
                Bar(
                    timestamp=pd.to_datetime(row["time"], utc=True).strftime(
                        "%Y-%m-%dT%H:%M:%S.000000Z"
                    ),
                    open=_format_decimal(Decimal(str(row["open"]))),
                    high=_format_decimal(Decimal(str(row["high"]))),
                    low=_format_decimal(Decimal(str(row["low"]))),
                    close=_format_decimal(Decimal(str(row["close"]))),
                    volume=str(int(float(row["volume"])))
                    if float(row["volume"]) > 0
                    else "100",
                    source_sequence=idx,
                    flags=0,
                )
                for idx, row in df.iterrows()
            ]
        else:
            bars = [
                Bar(
                    timestamp=f"2026-08-28T10:0{i}:00.000000Z",
                    open=_format_decimal(Decimal(100) + Decimal(i) * Decimal("0.1")),
                    high=_format_decimal(
                        Decimal("100.5") + Decimal(i) * Decimal("0.1")
                    ),
                    low=_format_decimal(Decimal("99.5") + Decimal(i) * Decimal("0.1")),
                    close=_format_decimal(
                        Decimal("100.2") + Decimal(i) * Decimal("0.1")
                    ),
                    volume="100",
                    source_sequence=i,
                    flags=0,
                )
                for i in range(5)
            ]
    return data_aggregate_timeframes(
        bars,
        target_timeframe="M5",
        alignment_origin="UTC_MIDNIGHT",
    )


def example_tick_aggregation() -> list[Bar]:
    """Aggregate canonical ticks into M1 OHLCV bars using real tick data."""
    from pathlib import Path

    import pandas as pd

    csv_path = Path("data/raw/EURUSD_ticks.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path).head(6)
        ticks = [
            Tick(
                timestamp=pd.to_datetime(row["time"], utc=True).strftime(
                    "%Y-%m-%dT%H:%M:%S.000000Z"
                ),
                bid=_format_decimal(Decimal(str(row["bid"]))),
                ask=_format_decimal(Decimal(str(row["ask"]))),
                last=_format_decimal(
                    Decimal(str(row["last"]))
                    if row["last"] != 0
                    else Decimal(str(row["bid"]))
                ),
                volume=str(int(row["volume"])) if row["volume"] != 0 else "10",
                source_sequence=idx,
                flags=0,
            )
            for idx, row in df.iterrows()
        ]
    else:
        ticks = [
            Tick(
                timestamp=f"2026-08-28T10:00:{i * 10:02d}.000000Z",
                bid=_format_decimal(Decimal("1.1000") + Decimal(i) * Decimal("0.0001")),
                ask=_format_decimal(Decimal("1.1002") + Decimal(i) * Decimal("0.0001")),
                last=_format_decimal(
                    Decimal("1.1001") + Decimal(i) * Decimal("0.0001")
                ),
                volume="10",
                source_sequence=i,
                flags=0,
            )
            for i in range(6)
        ]
    source_bars = [
        Bar(
            timestamp=t.timestamp,
            open=t.last or t.bid,
            high=t.ask or t.bid,
            low=t.bid,
            close=t.last or t.bid,
            volume=t.volume or "1",
            source_sequence=t.source_sequence,
            flags=t.flags,
        )
        for t in ticks
    ]
    return list(
        data_aggregate_timeframes(
            source_bars,
            target_timeframe="M1",
            alignment_origin="UTC_MIDNIGHT",
        )
    )


async def main() -> None:
    """Executable usage scenario harness for FEAT-DATA-AGGREGATE_BARS."""
    # 1. FR-DATA-DEFINE_CUSTOM_TIMEFRAMES
    print(
        "[SCENARIO 1] FR-DATA-DEFINE_CUSTOM_TIMEFRAMES: "
        "Validating presets and custom timeframes..."
    )
    expected_m5_minutes = 5
    expected_m10_minutes = 10
    expected_h2_minutes = 120

    tf_m5 = data_define_custom_timeframes("M5")
    assert tf_m5.unit == "MINUTE" and tf_m5.multiple == expected_m5_minutes
    tf_m10 = data_define_custom_timeframes("M10")
    assert tf_m10.unit == "MINUTE" and tf_m10.multiple == expected_m10_minutes
    tf_h2 = data_define_custom_timeframes("H2")
    assert tf_h2.unit == "MINUTE" and tf_h2.multiple == expected_h2_minutes
    print(f" -> M5 parsed: {tf_m5}, M10 parsed: {tf_m10}, H2 parsed: {tf_h2}")

    # 2. FR-DATA-AGGREGATE_TIMEFRAMES
    print(
        "[SCENARIO 2] FR-DATA-AGGREGATE_TIMEFRAMES: Aggregating M1 bars to M5 and H1..."
    )
    m1_bars = [
        Bar(
            timestamp=f"2026-08-28T10:0{i}:00.000000Z",
            open=_format_decimal(Decimal(100) + Decimal(i) * Decimal("0.1")),
            high=_format_decimal(Decimal("100.5") + Decimal(i) * Decimal("0.1")),
            low=_format_decimal(
                Decimal(100)
                if i == 0
                else Decimal("99.9") + Decimal(i) * Decimal("0.1")
            ),
            close=_format_decimal(Decimal("100.2") + Decimal(i) * Decimal("0.1")),
            volume="100",
            spread_ticks="2",
            source_sequence=i,
            flags=0,
        )
        for i in range(5)
    ]
    m5_bars = data_aggregate_timeframes(
        m1_bars,
        target_timeframe="M5",
        alignment_origin="UTC_MIDNIGHT",
    )
    assert (
        len(m5_bars) == 1
        and m5_bars[0].open == "100"
        and m5_bars[0].close == "100.6"
        and Decimal(m5_bars[0].volume) == Decimal(500)
    )
    print(f" -> Successfully aggregated 5 M1 bars into 1 M5 bar: {m5_bars[0]}")

    # 3. FR-DATA-RECORD_AGGREGATION_LINEAGE
    print(
        "[SCENARIO 3] FR-DATA-RECORD_AGGREGATION_LINEAGE: "
        "Lineage tracking and version hashing..."
    )
    spec = AggregationSpec(
        spec_id=_generate_uuid7(),
        source_version_id=_generate_uuid7(),
        target_timeframe=tf_m5,
        session_version_id=_generate_uuid7(),
        calendar_version_id=_generate_uuid7(),
        timezone="UTC",
        alignment_origin="UTC_MIDNIGHT",
        gap_policy="ABSENT_EMPTY",
        algorithm_version="v1.0.0",
    )
    derived_id_1, hash_1 = data_record_aggregation_lineage(spec)
    print(f" -> Derived Version ID: {derived_id_1}, Hash: {hash_1[:16]}...")

    # Verify policy change changes hash
    spec_changed = AggregationSpec(
        spec_id=spec.spec_id,
        source_version_id=spec.source_version_id,
        target_timeframe=tf_m5,
        session_version_id=spec.session_version_id,
        calendar_version_id=spec.calendar_version_id,
        timezone="UTC",
        alignment_origin="SESSION_BOUNDARY",
        gap_policy="ABSENT_EMPTY",
        algorithm_version="v1.0.0",
    )
    derived_id_2, hash_2 = data_record_aggregation_lineage(spec_changed)
    assert derived_id_1 != derived_id_2 and hash_1 != hash_2
    print(" -> Changing policy produced different derived-version hash successfully.")

    # Service check
    print("[SERVICE] Verifying BarAggregationService...")
    service = BarAggregationService()
    req = AggregateBarsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="AGGREGATE",
        spec=spec,
    )
    res = await service.aggregate_bars(req)
    assert isinstance(res, AggregateBarsSuccess) and res.outcome == "SUCCESS"
    print(" -> Service AGGREGATE invocation succeeded.")

    print("\n--- Additional Resampling & Aggregation Examples ---")
    resampled = example_resampling(m1_bars)
    print(f"  * example_resampling: generated {len(resampled)} M5 bar(s)")
    tick_aggr = example_tick_aggregation()
    print(f"  * example_tick_aggregation: generated {len(tick_aggr)} M1 bar(s)")

    print("=" * 80)
    print("ALL SCENARIOS PASSED")
    print("=" * 80)


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
