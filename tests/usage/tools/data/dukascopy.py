"""Usage example for Dukascopy data tools.

Run from the project root:

    python tests/usage/tools/data/dukascopy.py

This example performs real read-only network calls to Dukascopy.
"""

from __future__ import annotations

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) in sys.path:
    sys.path.remove(str(CURRENT_DIR))

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.data import (
    dukascopy_data_list_symbols,
    dukascopy_data_load,
    dukascopy_data_resolve_instrument,
)


def main() -> None:
    """Demonstrate safe agent-style use of Dukascopy tools."""
    request_id = "usage-dukascopy-001"

    resolved = dukascopy_data_resolve_instrument("EURUSD", request_id=request_id)
    if resolved["status"] == "success":
        print("Resolved instrument:", resolved["data"]["instrument"])
    else:
        print("Resolve error:", resolved["error"])
        return

    symbols = dukascopy_data_list_symbols(pattern="EUR*", request_id=request_id)
    if symbols["status"] == "success":
        print(f"Matched {symbols['data']['count']} EUR-related symbols")
    else:
        print("Symbol list error:", symbols["error"])

    bars = dukascopy_data_load(
        symbol="EURUSD",
        timeframe="M1",
        count=100,
        cache=True,
        request_id=request_id,
    )
    if bars["status"] == "success":
        print(
            "Loaded bars:",
            bars["data"]["row_count"],
            "from",
            bars["data"]["start_at"],
            "to",
            bars["data"]["end_at"],
        )
    else:
        print("Load error:", bars["error"])


if __name__ == "__main__":
    main()
