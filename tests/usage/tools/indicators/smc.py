"""Usage example for Smart Money Concepts tools."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.indicators import bos_choch, fvg, previous_high_low, swing_highs_lows


def main() -> None:
    """Run SMC tools with confirmed-only no-lookahead defaults."""
    data = pd.DataFrame(
        {
            "open": [10, 11, 12, 13, 12, 14, 15, 16],
            "high": [11, 12, 13, 14, 13, 15, 16, 17],
            "low": [9, 10, 11, 12, 11, 13, 14, 15],
            "close": [10.5, 11.5, 12.5, 13.5, 12.5, 14.5, 15.5, 16.5],
            "volume": [100, 110, 120, 130, 125, 140, 150, 160],
        }
    )
    request_id = "usage-smc-001"
    for tool in (fvg, swing_highs_lows, bos_choch, previous_high_low):
        result = tool(data, request_id=request_id)
        print(result["metadata"]["tool_name"], result["status"])


if __name__ == "__main__":
    main()
