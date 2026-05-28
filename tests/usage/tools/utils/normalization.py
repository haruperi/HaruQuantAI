"""
Usage example for tools.utils.normalization.

Run from the project root:

    python tests/usage/tools/utils/normalization.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import (
    ensure_dir,
    evaluate_board_baseline_freshness,
    evaluate_freshness,
    normalize_timestamp,
)
from tools.utils.normalization import FixedClock

request_id = "usage-normalization-001"

timestamp_result = normalize_timestamp(
    "2026-01-01T03:00:00+03:00",
    output="iso",
    request_id=request_id,
)
print(timestamp_result["data"])

checked_at = datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc)
freshness_result = evaluate_freshness(
    "2026-01-01T00:00:05Z",
    max_age_seconds=10,
    clock=FixedClock(checked_at),
    request_id=request_id,
)
print(freshness_result["data"]["is_fresh"])

with TemporaryDirectory() as tmp:
    root = Path(tmp)
    directory_result = ensure_dir(
        root / "reports", allowed_root=root, request_id=request_id
    )
    print(directory_result["data"])

board_result = evaluate_board_baseline_freshness(
    {
        "best_bid_ask_tick": checked_at - timedelta(seconds=1),
        "risk_decision": checked_at - timedelta(seconds=5),
    },
    clock=FixedClock(checked_at),
    request_id=request_id,
)
print(board_result["data"]["valid"])
