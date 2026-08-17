"""Unit tests for Data domain MT5 multi-symbol snapshot streams."""

from __future__ import annotations

import pytest
from app.services.data.market_events.mt5_snapshots import (
    _SnapshotRequest,
)


def test_mt5_snapshot_request_validation() -> None:
    """Verify _SnapshotRequest symbol uniqueness and count validation."""
    req = _SnapshotRequest(
        symbols=("EURUSD", "GBPUSD"),
        request_id="req-100",
    )
    assert req.symbols == ("EURUSD", "GBPUSD")
    assert req.request_id == "req-100"

    with pytest.raises(ValueError, match="snapshot symbol count is outside bounds"):
        _SnapshotRequest(symbols=(), request_id="req-101")

    with pytest.raises(ValueError, match="snapshot symbols must be unique"):
        _SnapshotRequest(symbols=("EURUSD", "EURUSD"), request_id="req-102")

    with pytest.raises(ValueError, match="request_id must be trimmed"):
        _SnapshotRequest(symbols=("EURUSD",), request_id="  ")
