"""WF-DATA-005: generate deterministic synthetic fixture data."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    SyntheticRequest,
    generate_synthetic_bars,
    generate_synthetic_ticks,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-005"
STAGES = (
    "Validate bounded synthetic parameters and an explicit seed.",
    "Generate canonical bars through the approved GBM method.",
    "Generate canonical ticks with identical deterministic inputs.",
    "Verify repeatability and fixture-only provenance.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute deterministic synthetic generation."""
    print(f"{WORKFLOW_ID} — Synthetic Generation")
    print("INPUT BOUNDARY — bounded GBM parameters and explicit seed")

    # Stage 1 — Validate bounded synthetic parameters and an explicit seed.
    _stage(1)
    common = {
        "symbol": "EURUSD",
        "start": datetime(2026, 1, 1, tzinfo=UTC),
        "record_count": 10,
        "method": "gbm",
        "seed": 42,
        "parameters": {
            "mu": Decimal("0.02"),
            "sigma": Decimal("0.10"),
            "start_val": Decimal("1.10"),
        },
        "precision_policy": "decimal_string",
    }

    # Stage 2 — Generate canonical bars through the approved GBM method.
    _stage(2)
    bar_request = SyntheticRequest(
        **common,
        data_kind="bars",
        timeframe="H1",
        request_id=generate_id("req"),
    )
    bars = generate_synthetic_bars(bar_request)

    # Stage 3 — Generate canonical ticks with identical deterministic inputs.
    _stage(3)
    tick_request = SyntheticRequest(
        **common,
        data_kind="ticks",
        request_id=generate_id("req"),
    )
    ticks = generate_synthetic_ticks(tick_request)

    # Stage 4 — Verify repeatability and fixture-only provenance.
    _stage(4)
    repeated = generate_synthetic_bars(
        bar_request.model_copy(update={"request_id": generate_id("req")})
    )
    assert bars.records == repeated.records
    print("Deterministic counts:", bars.record_count, ticks.record_count)
    print("OUTPUT BOUNDARY — fixture-only canonical bars and ticks")


if __name__ == "__main__":
    main()
