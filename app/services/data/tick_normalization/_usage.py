"""Executable usage demonstration harness for Tick Normalization."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from app.contracts.data.models import (
    NormalizeTicksRequest,
    NormalizeTicksSuccess,
    Tick,
)
from app.services.data.tick_normalization.tick_normalization import (
    TickNormalizationService,
    data_preserve_tick_fields,
)

_EXPECTED_TICK_COUNT = 3
_FIRST_SEQ = 1
_SECOND_SEQ = 2


async def main() -> None:
    """Executable usage scenario harness for FR-DATA-PRESERVE_TICK_FIELDS."""
    print("=" * 80)
    print("Tick Normalization (FEAT-DATA-NORMALIZE_TICKS) Scenario Harness")
    print("=" * 80)
    print("[SCENARIO] FR-DATA-PRESERVE_TICK_FIELDS: Normalizing tick batch...")
    service = TickNormalizationService()
    ts_now = "2026-08-28T12:00:00.000000Z"

    # Batch with duplicate timestamps preserved by source_sequence
    ticks = (
        Tick(
            timestamp=ts_now,
            bid="1.1",
            ask="1.10005",
            last="1.10002",
            volume="100",
            source_sequence=1,
            flags=0,
        ),
        Tick(
            timestamp=ts_now,
            bid="1.10001",
            ask="1.10006",
            last="1.10003",
            volume="250",
            source_sequence=2,
            flags=1,
        ),
        Tick(
            timestamp=ts_now,
            bid="1.10002",
            ask="1.10007",
            last=None,
            volume=None,
            source_sequence=3,
            flags=0,
        ),
    )

    norm_ticks, findings = data_preserve_tick_fields(ticks)
    assert len(norm_ticks) == _EXPECTED_TICK_COUNT
    assert norm_ticks[0].source_sequence == _FIRST_SEQ
    assert norm_ticks[1].source_sequence == _SECOND_SEQ
    assert len(findings) == 0

    req_id = "018f6e2b-1111-7000-8000-000000000001"
    snap_id = "018f6e2b-2222-7000-8000-000000000002"
    request = NormalizeTicksRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="NORMALIZE",
        ticks=ticks,
    )

    result = await service.normalize_ticks(request)
    assert isinstance(result, NormalizeTicksSuccess)

    print(f"[SCENARIO SUCCESS] Normalized {len(norm_ticks)} ticks with 0 findings.")

    print("\n--- Additional Real Tick Normalization Example ---")
    norm_real, findings_real = example_tick_model_real()
    print(
        f"  * example_tick_model_real: normalized {len(norm_real)} ticks, "
        f"findings={len(findings_real)}"
    )

    print("=" * 80)


def example_tick_model_real(
    sample_ticks: tuple[Tick, ...] | None = None,
) -> tuple[tuple[Tick, ...], tuple[Any, ...]]:
    """Normalize supplied genuine-tick-shaped evidence using real tick data."""
    if sample_ticks is None:
        from pathlib import Path

        import pandas as pd

        csv_path = Path("data/raw/EURUSD_ticks.csv")
        if csv_path.exists():
            df = pd.read_csv(csv_path).head(2)
            ticks = tuple(
                Tick(
                    timestamp=pd.to_datetime(row["time"], utc=True).strftime(
                        "%Y-%m-%dT%H:%M:%S.000000Z"
                    ),
                    bid=str(Decimal(str(row["bid"])).normalize()),
                    ask=str(Decimal(str(row["ask"])).normalize()),
                    last=str(Decimal(str(row["last"])).normalize())
                    if row["last"] != 0
                    else str(Decimal(str(row["bid"])).normalize()),
                    volume=str(int(row["volume"])) if row["volume"] != 0 else "100",
                    source_sequence=idx + 1,
                    flags=0,
                )
                for idx, row in df.iterrows()
            )
            return data_preserve_tick_fields(ticks)
    ticks = sample_ticks or (
        Tick(
            timestamp="2026-08-28T12:00:00.000000Z",
            bid="1.1",
            ask="1.10005",
            last="1.10002",
            volume="100",
            source_sequence=1,
            flags=0,
        ),
        Tick(
            timestamp="2026-08-28T12:00:00.000000Z",
            bid="1.10001",
            ask="1.10006",
            last="1.10003",
            volume="250",
            source_sequence=2,
            flags=1,
        ),
    )
    return data_preserve_tick_fields(ticks)


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
