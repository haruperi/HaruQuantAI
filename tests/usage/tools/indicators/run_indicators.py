"""Usage example for the HaruQuant indicators domain."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.indicators import atr, fvg, rsi, sma


def main() -> None:
    """Run a small indicator workflow using official domain imports."""
    data = pd.DataFrame(
        {
            "open": [1.10, 1.11, 1.12, 1.13, 1.12, 1.14],
            "high": [1.12, 1.13, 1.14, 1.15, 1.14, 1.16],
            "low": [1.09, 1.10, 1.11, 1.12, 1.11, 1.13],
            "close": [1.11, 1.12, 1.13, 1.14, 1.13, 1.15],
            "volume": [100, 120, 140, 130, 150, 160],
        },
        index=pd.date_range("2026-01-01", periods=6, freq="h"),
    )

    request_id = "usage-indicators-001"
    for tool, kwargs in [
        (sma, {"period": 3}),
        (rsi, {"period": 3}),
        (atr, {"period": 3}),
        (fvg, {"confirmed_only": True}),
    ]:
        result = tool(data, request_id=request_id, **kwargs)
        if result["status"] == "success":
            print(f"{result['metadata']['tool_name']} rows: {len(result['data'])}")
        else:
            print(result["error"])


if __name__ == "__main__":
    main()
