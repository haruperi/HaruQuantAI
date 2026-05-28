"""Shared fixtures for indicator tool tests."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture()
def ohlcv() -> pd.DataFrame:
    """Return deterministic OHLCV test data."""
    return pd.DataFrame(
        {
            "open": [10, 11, 12, 13, 12, 14, 15, 16, 15, 17, 18, 19, 20, 21, 22],
            "high": [11, 12, 13, 14, 13, 15, 16, 17, 16, 18, 19, 20, 21, 22, 23],
            "low": [9, 10, 11, 12, 11, 13, 14, 15, 14, 16, 17, 18, 19, 20, 21],
            "close": [
                10.5,
                11.5,
                12.5,
                13.5,
                12.5,
                14.5,
                15.5,
                16.5,
                15.5,
                17.5,
                18.5,
                19.5,
                20.5,
                21.5,
                22.5,
            ],
            "volume": [
                100,
                110,
                120,
                130,
                125,
                140,
                150,
                160,
                155,
                170,
                180,
                190,
                200,
                210,
                220,
            ],
        },
        index=pd.date_range("2026-01-01", periods=15, freq="D"),
    )


def assert_standard_response(response: dict, tool_name: str) -> None:
    """Assert a response follows the HaruQuant tool schema."""
    assert set(response) == {"status", "message", "data", "error", "metadata"}
    assert response["status"] in {"success", "error"}
    metadata = response["metadata"]
    assert metadata["tool_name"] == tool_name
    assert metadata["tool_category"] == "indicators"
    assert metadata["tool_risk_level"] == "low"
    assert metadata["read_only"] is True
    assert metadata["writes_file"] is False
    assert metadata["modifies_database"] is False
    assert metadata["places_trade"] is False
    assert metadata["requires_network"] is False
    assert isinstance(metadata["execution_ms"], float)
