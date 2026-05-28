"""Test fixtures for strategy domain tests."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture()
def ohlc_data() -> pd.DataFrame:
    """Return deterministic OHLC data suitable for EMA crossover tests."""
    rows = []
    close = 1.0000
    for index in range(260):
        if index < 130:
            close -= 0.0002
        else:
            close += 0.0005
        rows.append(
            {
                "open": close - 0.0001,
                "high": close + 0.0002,
                "low": close - 0.0002,
                "close": close,
                "volume": 1000 + index,
            }
        )
    return pd.DataFrame(
        rows, index=pd.date_range("2026-01-01", periods=len(rows), freq="h")
    )
