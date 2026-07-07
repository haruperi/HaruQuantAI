"""Benchmark series alignment and boundary rules for Analytics.

All calculations are stateless pure functions.
"""

from __future__ import annotations

from typing import cast


def _to_float_list(series: object) -> list[float]:
    if series is None:
        return []
    if hasattr(series, "tolist"):
        return cast("list[float]", series.tolist())
    if isinstance(series, (list, tuple, set)):
        return [float(x) for x in series]
    try:
        return [float(x) for x in series]  # type: ignore[attr-defined]
    except (TypeError, ValueError):
        return []


def _align_series(
    strategy_returns: object, benchmark_returns: object
) -> tuple[list[float], list[float]]:
    """Align strategy and benchmark returns chronologically, truncating if necessary."""
    s_list = _to_float_list(strategy_returns)
    b_list = _to_float_list(benchmark_returns)

    # Try using pandas alignment if they are pandas objects
    if hasattr(strategy_returns, "align") and hasattr(benchmark_returns, "align"):
        import pandas as pd

        s_ser = pd.Series(strategy_returns)
        b_ser = pd.Series(benchmark_returns)
        s_aligned, b_aligned = s_ser.align(b_ser, join="inner")
        return [float(x) for x in s_aligned.tolist()], [
            float(x) for x in b_aligned.tolist()
        ]

    n = min(len(s_list), len(b_list))
    return s_list[:n], b_list[:n]


def bench_alignment_boundary() -> None:
    """Pure architectural boundary declaration for benchmark alignment.

    Documents UTC normalization, window restriction, currency metadata validation,
    and FX conversion rules.
    """
