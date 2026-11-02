"""Bounded historical quality analysis.

Description:
    Audits recorded observations, scans expected timestamps in bounded chunks,
    and returns complete counts, daily coverage and one issue page.
Purpose:
    FEAT-DATA-QUALITY: Review long histories without a full expected-date grid.
Key Capabilities:
    - FR-DATA-QUALITY-bounded-analysis: Log complete counts and returned page size.
Python API Usage:
    Call analyze_quality(frame, timeframe, calendar, limit=500, offset=0).
CLI Usage:
    uv run pytest tests/workspace/data_manager/test_data_review.py --no-cov
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from app.core.data.contracts import TradingSession
from app.core.host.logging import get_logger

logger = get_logger(__name__)
EXPECTED_CHUNK = 65_536
SPIKE_THRESHOLD = 0.1
MAX_ISSUE_PAGE = 1000


def _expected_chunks(
    index: Any, timeframe: str, calendar: TradingSession | None
) -> Iterator[Any]:
    """Yield at most one bounded block of expected timestamps at a time."""
    if timeframe == "MN1" or timeframe[:1] not in {"M", "H", "D"}:
        return
    unit = {"M": "min", "H": "h", "D": "D"}[timeframe[0]]
    step = pd.Timedelta(f"{int(timeframe[1:])}{unit}")
    if step <= pd.Timedelta(0):
        raise ValueError("Invalid quality timeframe")
    start, end = index.min(), index.max()
    periods = int((end - start) // step) + 1
    for position in range(0, periods, EXPECTED_CHUNK):
        expected = pd.date_range(
            start + position * step,
            periods=min(EXPECTED_CHUNK, periods - position),
            freq=step,
        )
        if calendar:
            expected = expected[
                [calendar.is_within_session(s.to_pydatetime()) for s in expected]
            ]
        yield expected


def analyze_quality(
    frame: pd.DataFrame,
    timeframe: str,
    calendar: TradingSession | None,
    *,
    limit: int = 500,
    offset: int = 0,
) -> dict[str, Any]:
    """Count every issue while retaining only the requested issue page."""
    if not 0 <= limit <= MAX_ISSUE_PAGE or offset < 0:
        raise ValueError("Invalid quality pagination")
    counts: Counter[str] = Counter()
    days: dict[str, dict[str, int]] = {}
    issues: list[dict[str, Any]] = []
    issue_count = 0

    def daily(index: Any, field: str) -> None:
        for stamp, count in index.normalize().value_counts().items():
            day = days.setdefault(
                stamp.strftime("%Y-%m-%d"),
                {"observed": 0, "expected": 0, "issues": 0},
            )
            day[field] += int(count)

    def collect(index: Any, kind: str) -> None:
        nonlocal issue_count
        count = len(index)
        counts[kind] += count
        daily(index, "issues")
        first = max(0, offset - issue_count)
        remaining = limit - len(issues)
        issues.extend(
            {"date": stamp.isoformat(), "kind": kind}
            for stamp in index[first : first + remaining]
        )
        issue_count += count

    if not frame.empty:
        frame = frame.sort_index()
        daily(frame.index, "observed")
        collect(frame.index[frame.index.duplicated()], "Duplicate")
        tick = "Bid" in frame
        invalid = frame.isna().any(axis=1)
        if tick:
            invalid |= frame.Ask < frame.Bid
        else:
            invalid |= (frame.High < frame[["Open", "Close", "Low"]].max(axis=1)) | (
                frame.Low > frame[["Open", "Close", "High"]].min(axis=1)
            )
        collect(frame.index[invalid], "Invalid quote" if tick else "Bad OHLC")
        close = (frame.Bid + frame.Ask) / 2 if tick else frame.Close
        collect(
            frame.index[close.pct_change(fill_method=None).abs() > SPIKE_THRESHOLD],
            "Spike",
        )
        if not tick:
            observed = frame.index.unique()
            for expected in _expected_chunks(frame.index, timeframe, calendar):
                daily(expected, "expected")
                if len(expected):
                    left = observed.searchsorted(expected[0], side="left")
                    right = observed.searchsorted(expected[-1], side="right")
                    collect(expected.difference(observed[left:right]), "Gap")

    result = {
        "total": len(frame),
        "issues": issues,
        "issue_count": issue_count,
        "counts": dict(counts),
        "percents": {
            kind: count * 100 / len(frame) if len(frame) else 0
            for kind, count in counts.items()
        },
        "coverage": [{"date": date, **days[date]} for date in sorted(days)],
        "gap_policy": "no observations"
        if frame.empty
        else ("saved session" if calendar else "continuous (no session assigned)"),
        "spike_threshold": SPIKE_THRESHOLD,
        "offset": offset,
        "limit": limit,
    }
    logger.info(
        "FR-DATA-QUALITY-bounded-analysis: observations=%d issues=%d page=%d",
        len(frame),
        issue_count,
        len(issues),
    )
    return result
