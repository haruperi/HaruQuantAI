"""Usage example for FEAT-DATA-15: the SQX/QuantDataManager source.

Demonstrates the public source operations against the configured
QuantDataManager workspace: symbol discovery, a bounded date-filtered M1
read, a bounded tick read, and the reference synchronisation. Live ``.dat``
payload reads run only when ``HARU_SQX_LIVE=1`` so the program stays
hermetic by default.

Run directly:
    HARU_SQX_LIVE=1 uv run python tests/data/usage/features/15_sqx_source.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    list_sqx_symbols,
    read_sqx_m1,
    read_sqx_ticks,
    sync_quantdata_reference,
)


def main() -> None:
    """Exercise the SQX source feature through its public API."""
    request_id = generate_id("req")

    symbols = list_sqx_symbols(request_id=request_id)
    print(f"symbols discovered: {len(symbols)}")
    print(symbols.head(3).to_string(index=False))

    if os.environ.get("HARU_SQX_LIVE") != "1":
        print("\nHARU_SQX_LIVE not set; skipping live .dat payload reads.")
    else:
        bars = read_sqx_m1(
            "EURUSD", start="2021-01-04", end="2021-01-05", request_id=request_id
        )
        print(f"\nEURUSD M1 bars (2021-01-04..05): {len(bars)}")
        print(bars.head(2).to_string())
        ticks = read_sqx_ticks(
            "EURUSD", start="2021-01-04", max_ticks=1000, request_id=request_id
        )
        print(f"\nEURUSD ticks (bounded 1000): {len(ticks)}")
        print(ticks.head(2).to_string())

    summary = sync_quantdata_reference(request_id=request_id)
    print(f"\nreference sync: {summary}")


if __name__ == "__main__":
    main()
