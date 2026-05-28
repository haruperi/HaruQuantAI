"""Unit tests for tools.utils.normalization."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from tools.utils.normalization import (
    FixedClock,
    ensure_dir,
    ensure_parent_dir,
    evaluate_board_baseline_freshness,
    evaluate_freshness,
    format_timestamp_z,
    is_stale,
    normalize_path,
    normalize_timestamp,
    normalize_timezone_for_series,
    parse_datetime_value,
    to_naive_utc_datetime,
    to_utc,
    to_utc_datetime,
)


def assert_tool_schema(result: dict) -> None:
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["metadata"]["tool_name"]
    assert result["metadata"]["tool_category"] == "utils"
    assert isinstance(result["metadata"]["execution_ms"], float)


def test_normalize_path_inside_allowed_root(tmp_path: Path) -> None:
    result = normalize_path(
        "file.txt", base=tmp_path, allowed_root=tmp_path, request_id="req-001"
    )

    assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["data"]["inside_allowed_root"] is True
    assert result["metadata"]["request_id"] == "req-001"


def test_normalize_path_blocks_outside_allowed_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"

    result = normalize_path(outside, allowed_root=tmp_path)

    assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "PERMISSION_DENIED"


def test_path_tools_reject_invalid_or_outside_inputs(tmp_path: Path) -> None:
    invalid_path = normalize_path("", allowed_root=tmp_path)
    outside_parent = ensure_parent_dir(
        tmp_path.parent / "report.json", allowed_root=tmp_path
    )
    outside_dir = ensure_dir(tmp_path.parent / "reports", allowed_root=tmp_path)

    assert invalid_path["status"] == "error"
    assert invalid_path["error"]["code"] == "INVALID_INPUT"
    assert outside_parent["status"] == "error"
    assert outside_parent["error"]["code"] == "PERMISSION_DENIED"
    assert outside_dir["status"] == "error"
    assert outside_dir["error"]["code"] == "PERMISSION_DENIED"


def test_ensure_dir_creates_directory_inside_allowed_root(tmp_path: Path) -> None:
    target = tmp_path / "reports"

    result = ensure_dir(target, allowed_root=tmp_path)

    assert_tool_schema(result)
    assert result["status"] == "success"
    assert target.exists()
    assert result["metadata"]["tool_risk_level"] == "medium"
    assert result["metadata"]["writes_file"] is True


def test_ensure_parent_dir_creates_parent_inside_allowed_root(tmp_path: Path) -> None:
    target = tmp_path / "reports" / "report.json"

    result = ensure_parent_dir(target, allowed_root=tmp_path)

    assert_tool_schema(result)
    assert result["status"] == "success"
    assert target.parent.exists()


def test_normalize_timestamp_outputs_iso_epoch_seconds_and_ms() -> None:
    value = "2026-01-01T00:00:00Z"

    iso = normalize_timestamp(value, output="iso")
    epoch_s = normalize_timestamp(value, output="epoch_s")
    epoch_ms = normalize_timestamp(value, output="epoch_ms")

    assert iso["data"]["value"] == "2026-01-01T00:00:00Z"
    assert isinstance(epoch_s["data"]["value"], int)
    assert epoch_ms["data"]["value"] == epoch_s["data"]["value"] * 1000


def test_normalize_timestamp_invalid_output() -> None:
    result = normalize_timestamp("2026-01-01T00:00:00Z", output="bad")  # type: ignore[arg-type]

    assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_parse_datetime_value_and_to_utc_datetime() -> None:
    parsed = parse_datetime_value("2026-01-01T03:00:00+03:00")
    utc_value = to_utc_datetime(parsed)

    assert utc_value.isoformat() == "2026-01-01T00:00:00+00:00"


def test_datetime_helpers_cover_epoch_naive_and_invalid_inputs() -> None:
    epoch_ms = parse_datetime_value(1_767_225_600_000)
    naive = to_naive_utc_datetime("2026-01-01T03:00:00+03:00")

    assert epoch_ms.tzinfo == timezone.utc
    assert naive.tzinfo is None
    assert format_timestamp_z(None) is None
    assert format_timestamp_z("2026-01-01T00:00:00+00:00") == "2026-01-01T00:00:00Z"
    assert to_utc(datetime(2026, 1, 1, tzinfo=timezone.utc)).tzinfo == timezone.utc

    with pytest.raises(TypeError):
        to_utc("2026-01-01")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        parse_datetime_value("")
    with pytest.raises(ValueError):
        parse_datetime_value("not-a-date")


def test_normalize_timezone_for_series_and_index() -> None:
    index = pd.DatetimeIndex(["2026-01-01T00:00:00Z"])
    series = pd.Series(["2026-01-01T03:00:00+03:00"])

    normalized_index = normalize_timezone_for_series(index, target_tz="Asia/Dubai")
    normalized_series = normalize_timezone_for_series(series, make_naive=True)

    assert str(normalized_index.tz) == "Asia/Dubai"
    assert normalized_series.dt.tz is None

    with pytest.raises(ValueError):
        normalize_timezone_for_series(["2026-01-01"])


def test_evaluate_freshness_fresh_stale_and_boundary() -> None:
    checked_at = datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc)

    fresh = evaluate_freshness(
        "2026-01-01T00:00:05Z",
        max_age_seconds=10,
        clock=FixedClock(checked_at),
    )
    stale = evaluate_freshness(
        "2025-12-31T23:59:00Z",
        max_age_seconds=10,
        clock=FixedClock(checked_at),
    )
    boundary = evaluate_freshness(
        "2026-01-01T00:00:00Z",
        max_age_seconds=10,
        clock=FixedClock(checked_at),
    )

    assert fresh["data"]["is_fresh"] is True
    assert stale["data"]["is_stale"] is True
    assert boundary["data"]["is_fresh"] is True


def test_evaluate_freshness_rejects_negative_ttl() -> None:
    result = evaluate_freshness("2026-01-01T00:00:00Z", max_age_seconds=-1)

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_is_stale_returns_boolean_payload() -> None:
    checked_at = datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc)

    result = is_stale(
        "2025-12-31T23:59:00Z",
        max_age_seconds=5,
        clock=FixedClock(checked_at),
    )

    assert result["data"]["is_stale"] is True


def test_board_baseline_all_valid() -> None:
    checked_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    result = evaluate_board_baseline_freshness(
        {
            "best_bid_ask_tick": checked_at - timedelta(seconds=1),
            "risk_decision": checked_at - timedelta(seconds=5),
        },
        clock=FixedClock(checked_at),
    )

    assert result["status"] == "success"
    assert result["data"]["valid"] is True


def test_board_baseline_stale_artifact_invalidates() -> None:
    checked_at = datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc)

    result = evaluate_board_baseline_freshness(
        {"best_bid_ask_tick": checked_at - timedelta(seconds=10)},
        clock=FixedClock(checked_at),
    )

    assert result["data"]["valid"] is False
    assert result["data"]["stale_artifacts"] == ["best_bid_ask_tick"]


def test_board_baseline_material_change_invalidates() -> None:
    checked_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    result = evaluate_board_baseline_freshness(
        {"risk_decision": checked_at},
        proposal_materially_changed=True,
        clock=FixedClock(checked_at),
    )

    assert result["data"]["valid"] is False


def test_board_baseline_rejects_empty_mapping_and_tracks_pause_ttl() -> None:
    checked_at = datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc)

    empty = evaluate_board_baseline_freshness({})
    paused = evaluate_board_baseline_freshness(
        {"best_bid_ask_tick": checked_at},
        workflow_paused_at=checked_at - timedelta(seconds=3),
        clock=FixedClock(checked_at),
    )

    assert empty["status"] == "error"
    assert empty["error"]["code"] == "INVALID_INPUT"
    assert paused["data"]["valid"] is False
    assert paused["data"]["workflow_pause_exceeded_shortest_ttl"] is True


def test_board_baseline_invalid_artifact() -> None:
    result = evaluate_board_baseline_freshness({"unknown": "2026-01-01T00:00:00Z"})

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"
