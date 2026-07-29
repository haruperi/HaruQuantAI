"""WF-DATA-019: classify named sessions at a genuine MT5 observation time."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_active_market_sessions_request,
    get_active_market_sessions,
    get_market_data,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime, market_request

WORKFLOW_ID = "WF-DATA-019"
STAGES = (
    "Retrieve a genuine MT5 observation timestamp.",
    "Submit the exact symbol and aware UTC instant.",
    "Classify regional sessions with DST-aware definitions.",
    "Return labels structurally separated from tradability.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute analytical named-session classification."""
    print(f"{WORKFLOW_ID} — Analytical Named-Session Classification")
    print("INPUT BOUNDARY — exact symbol and genuine aware UTC instant")

    with (
        tempfile.TemporaryDirectory(prefix="wf-data-019-") as directory,
        isolated_runtime(Path(directory)),
    ):
        request_id = generate_id("req")

        # Stage 1 — Retrieve a genuine MT5 observation timestamp.
        _stage(1)
        bars_resp = get_market_data(market_request("bars", timeframe="M1", limit=1))
        bars = unwrap_data_response(
            bars_resp, operation="get_market_data", request_id=request_id
        )

        # Stage 2 — Submit the exact symbol and aware UTC instant.
        _stage(2)
        request = build_active_market_sessions_request(
            symbol=bars.symbol,
            at=bars.records[-1].timestamp,
            request_id=request_id,
        )

        # Stage 3 — Classify regional sessions with DST-aware definitions.
        _stage(3)
        sessions_resp = get_active_market_sessions(request)
        sessions = unwrap_data_response(
            sessions_resp, operation="get_active_market_sessions", request_id=request_id
        )

        # Stage 4 — Return labels structurally separated from tradability.
        _stage(4)
        assert not hasattr(sessions, "is_open")
        print("Analytical labels:", sessions.sessions)
    print("OUTPUT BOUNDARY — DST-aware liquidity labels with no trading authority")


if __name__ == "__main__":
    main()
