"""Usage example for the LEXLB labeling tool."""

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

from tools.data import labeler_lexlb


def main() -> None:
    """Generate supervised labels for a simple close-price series."""

    close = pd.Series(
        [100, 104, 110, 103, 95, 101, 108],
        index=pd.date_range("2024-01-01", periods=7, freq="D"),
        name="close",
    )

    result = labeler_lexlb(
        data=close,
        up_threshold=0.05,
        down_threshold=0.05,
        request_id="usage-labeling-001",
    )

    if result["status"] == "success":
        print(result["data"]["summary"])
    else:
        print(result["error"])


if __name__ == "__main__":
    main()
