"""Unit tests for the TrendSnapshot/StructureSnapshot/OrderFlowSnapshot builders."""

from datetime import UTC, datetime

import pytest
from app.services.indicators.snapshots.snapshot import (
    build_order_flow_snapshot,
    build_structure_snapshot,
    build_trend_snapshot,
)

from tests.indicators.helpers import assert_error, unwrap_response

_AS_OF = datetime(2026, 1, 1, tzinfo=UTC)


def _common_kwargs() -> dict[str, object]:
    """Shared valid v2-envelope keyword arguments for every category builder."""
    return {
        "snapshot_id": "snap-1",
        "indicator_version": "1.0.0",
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
        "symbol": "EURUSD",
        "venue": "mt5",
        "timeframe": "M5",
        "as_of": _AS_OF,
        "available_at": _AS_OF,
        "source_start": _AS_OF,
        "source_end": _AS_OF,
        "source_record_count": 10,
        "source_dataset_id": "dataset-1",
        "source_dataset_hash": "a" * 64,
        "state": "VALID",
        "completeness": 1.0,
        "confidence": 1.0,
        "data_health": "ok",
        "warmup_state": "ready",
        "parameters": {},
    }


def test_build_trend_snapshot_accepts_required_keys() -> None:
    """TrendSnapshot validates with its required value keys present."""
    result = unwrap_response(
        build_trend_snapshot(
            values={
                "direction": 1.0,
                "strength": 25.0,
                "adx": 30.0,
                "plus_di": 20.0,
                "minus_di": 10.0,
            },
            **_common_kwargs(),
        )
    )
    assert result["category"] == "trend"
    assert result["values"]["adx"] == pytest.approx(30.0)


def test_build_trend_snapshot_rejects_missing_required_key() -> None:
    """TrendSnapshot fails closed when a required value key is missing."""
    assert_error(
        build_trend_snapshot(values={"direction": 1.0}, **_common_kwargs()),
        "IND_INVALID_SNAPSHOT",
    )


def test_build_structure_snapshot_accepts_required_keys() -> None:
    """StructureSnapshot validates with its required value keys present."""
    result = unwrap_response(
        build_structure_snapshot(
            values={
                "pivot_high_price": 1.2,
                "pivot_low_price": 1.1,
                "donchian_upper": 1.25,
                "donchian_lower": 1.05,
                "anchored_vwap": 1.15,
            },
            **_common_kwargs(),
        )
    )
    assert result["category"] == "structure"


def test_build_order_flow_snapshot_accepts_required_keys() -> None:
    """OrderFlowSnapshot validates with its required value keys present."""
    result = unwrap_response(
        build_order_flow_snapshot(
            values={"cvd": 100.0, "aggressive_trade_imbalance": 0.2},
            **_common_kwargs(),
        )
    )
    assert result["category"] == "order_flow"
    assert result["indicator_id"] == "order_flow_snapshot"


def test_build_order_flow_snapshot_rejects_missing_required_key() -> None:
    """OrderFlowSnapshot fails closed when a required value key is missing."""
    assert_error(
        build_order_flow_snapshot(values={"cvd": 100.0}, **_common_kwargs()),
        "IND_INVALID_SNAPSHOT",
    )
