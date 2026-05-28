"""Usage example for HaruQuantAI MT5 data tools.

Run from the project root after configuring `.env` with MT5 credentials and
starting the Windows MetaTrader 5 terminal.
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

import pandas as pd

from tools.data import (
    mt5_connection_check,
    mt5_data_get_bars,
    mt5_data_list_symbol_details,
    mt5_data_list_symbols,
)

REQUEST_ID = "usage-mt5-001"


def _bars_to_dataframe(bars_result: dict) -> pd.DataFrame:
    """Convert a successful MT5 bars tool response into a DataFrame."""

    data = bars_result["data"]
    frame = pd.DataFrame(data["data"])
    return frame.set_index("timestamp") if "timestamp" in frame.columns else frame


def main() -> None:
    """Demonstrate safe MT5 tool usage from an agent-style workflow."""
    connection = mt5_connection_check(request_id=REQUEST_ID)
    if connection["status"] != "success":
        print("MT5 connection check failed:", connection["error"])
        return

    symbols = mt5_data_list_symbols(pattern="EUR*", request_id=REQUEST_ID)
    if symbols["status"] == "success":
        print(f"Found {symbols['data']['count']} EUR symbols")
    else:
        print("Symbol listing failed:", symbols["error"])

    bars = mt5_data_get_bars(
        symbol="EURUSD",
        timeframe="H1",
        count=100,
        request_id=REQUEST_ID,
    )
    if bars["status"] == "success":
        print(f"Loaded {bars['data']['rows']} EURUSD H1 bars")
        bars_frame = _bars_to_dataframe(bars)
        print("\nEURUSD H1 bars DataFrame preview:")
        print(bars_frame.head(10).to_string())
    else:
        print("Bar loading failed:", bars["error"])

    details = mt5_data_list_symbol_details(request_id=REQUEST_ID)
    if details["status"] == "success":
        print(f"Loaded metadata for {details['data']['count']} symbols")
    else:
        print("Symbol detail loading failed:", details["error"])


if __name__ == "__main__":
    main()
