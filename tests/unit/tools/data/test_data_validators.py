from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tools.data.validators import (
    DataQualityReport,
    prepare_ohlcv_data,
    validate_annotate_issues,
    validate_duplicate_ohlc_rows,
    validate_duplicates,
    validate_find_column,
    validate_find_columns,
    validate_flatlines,
    validate_gaps,
    validate_get_time_series,
    validate_issue_remediation_action,
    validate_issue_severity,
    validate_missing_timestamps,
    validate_monotonic_timestamps,
    validate_numeric_integrity,
    validate_ohlcv_quality,
    validate_price_sanity,
    validate_remediation_summary,
    validate_spikes,
    validate_spread,
    validate_timezone_awareness,
    validate_zero_volume,
)


def sample_df():
    return pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=5, freq="h", tz="UTC"),
            "open": [1.1, 1.2, 1.3, 1.4, 1.5],
            "high": [1.2, 1.3, 1.4, 1.5, 1.6],
            "low": [1.0, 1.1, 1.2, 1.3, 1.4],
            "close": [1.15, 1.25, 1.35, 1.45, 1.55],
            "volume": [10, 11, 12, 13, 14],
            "spread": [1, 1, 1, 1, 1],
        }
    )


def assert_tool_schema(result):
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["metadata"]["tool_name"] == "validate_ohlcv_quality"


def test_prepare_ohlcv_data_normalizes_lowercase_columns():
    prepared = prepare_ohlcv_data(sample_df())
    assert list(prepared.columns) == [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Spread",
    ]
    assert isinstance(prepared.index, pd.DatetimeIndex)


def test_validate_price_sanity_detects_high_low_violation():
    df = prepare_ohlcv_data(sample_df())
    df.loc[df.index[0], "High"] = 0.5
    ok, _, issues = validate_price_sanity(df)
    assert ok is False and any(i["check"] == "high_low" for i in issues)


def test_validate_spread_detects_negative_spread():
    df = prepare_ohlcv_data(sample_df())
    df.loc[df.index[0], "Spread"] = -1
    stats, issues = validate_spread(df)
    assert stats["min"] == -1.0 and any(
        i.get("issue") == "negative_spread" for i in issues
    )


def test_validate_ohlcv_quality_success():
    result = validate_ohlcv_quality(
        sample_df(), profile="research", request_id="req-data-test"
    )
    assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["metadata"]["request_id"] == "req-data-test"


def test_validate_ohlcv_quality_invalid_input():
    result = validate_ohlcv_quality([], profile="research")  # type: ignore[arg-type]
    assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_validate_ohlcv_quality_return_report():
    report = validate_ohlcv_quality(sample_df(), return_report=True)
    assert isinstance(report, DataQualityReport)
    assert report.total_rows == 5


def test_column_and_time_helpers_cover_missing_paths():
    df = sample_df()
    assert validate_find_column(df, "OPEN") == "open"
    assert validate_find_column(df, "missing") is None
    assert validate_find_columns(df, ["Open", "Close"]) == {
        "Open": "open",
        "Close": "close",
    }
    assert validate_get_time_series(prepare_ohlcv_data(df)) is not None
    assert validate_get_time_series(pd.DataFrame({"x": [1]})) is None


def test_prepare_ohlcv_data_errors_and_bid_ask_spread():
    with pytest.raises(TypeError):
        prepare_ohlcv_data([])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        prepare_ohlcv_data(pd.DataFrame())
    with pytest.raises(ValueError):
        prepare_ohlcv_data(pd.DataFrame({"open": [1], "high": [1], "low": [1]}))
    with pytest.raises(ValueError):
        prepare_ohlcv_data(
            pd.DataFrame(
                {"open": [1], "high": [1], "low": [1], "close": [1], "volume": [1]}
            )
        )

    df = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=2, freq="h"),
            "open": [1, 2],
            "high": [2, 3],
            "low": [0.5, 1.5],
            "close": [1.5, 2.5],
            "bid": [1.0, 2.0],
            "ask": [1.2, 2.3],
        }
    )
    prepared = prepare_ohlcv_data(df)
    assert prepared["Spread"].tolist() == pytest.approx([0.2, 0.3])


def test_numeric_price_and_timestamp_issue_helpers():
    df = prepare_ohlcv_data(sample_df())
    df["Open"] = df["Open"].astype(object)
    df.loc[df.index[0], "Open"] = "bad"
    df.loc[df.index[1], "High"] = np.inf
    cleaned, issues = validate_numeric_integrity(df)
    assert cleaned["Open"].isna().any()
    assert {issue["type"] for issue in issues} >= {"non_numeric", "infinite_values"}

    bad = prepare_ohlcv_data(sample_df())
    bad.loc[bad.index[0], "Open"] = -1
    bad.loc[bad.index[1], "Close"] = 0
    ok, _, price_issues = validate_price_sanity(bad)
    assert ok is False
    assert any(
        issue["type"] in {"price_sanity", "zero_price"} for issue in price_issues
    )

    unsorted = sample_df().iloc[[1, 0, 2, 3, 4]]
    rows, monotonic = validate_monotonic_timestamps(unsorted)
    assert len(rows) == 1
    assert monotonic[0]["type"] == "monotonic_timestamps"

    dup = pd.concat([sample_df(), sample_df().iloc[[0]]], ignore_index=True)
    duplicate_rows, duplicate_issues = validate_duplicates(dup)
    assert not duplicate_rows.empty
    assert duplicate_issues[0]["type"] == "duplicates"


def test_gap_missing_volume_spread_and_anomaly_helpers():
    df = sample_df().drop(index=2).reset_index(drop=True)
    gap_rows, gap_issues = validate_gaps(df, expected_frequency="1h")
    missing_rows, missing_issues = validate_missing_timestamps(
        df, expected_frequency="1h"
    )
    assert not gap_rows.empty
    assert gap_issues[0]["type"] == "gap"
    assert not missing_rows.empty
    assert missing_issues[0]["type"] == "missing_timestamps"

    prepared = prepare_ohlcv_data(sample_df())
    prepared.loc[prepared.index[0], "Volume"] = 0
    zero_rows, zero_issues = validate_zero_volume(prepared)
    assert len(zero_rows) == 1
    assert zero_issues[0]["type"] == "zero_volume"

    prepared.loc[prepared.index[1], "Spread"] = 99
    stats, spread_issues = validate_spread(prepared, max_allowed_spread=10)
    assert stats["max"] == 99.0
    assert any(issue.get("issue") == "max_allowed_spread" for issue in spread_issues)

    duplicated, duplicate_ohlc = validate_duplicate_ohlc_rows(prepared)
    assert duplicated.empty
    assert duplicate_ohlc == []

    flat = prepared.copy()
    flat["Close"] = 1.0
    flat_rows, flat_issues = validate_flatlines(flat, min_run_length=3)
    assert not flat_rows.empty
    assert flat_issues[0]["type"] == "flatline"

    spike = prepared.copy()
    spike.loc[spike.index[-1], "Close"] = 10.0
    _, spike_issues = validate_spikes(spike, z_score_threshold=1.0)
    assert spike_issues


def test_issue_annotation_quality_and_profile_paths():
    naive = prepare_ohlcv_data(
        sample_df().assign(time=pd.date_range("2026-01-01", periods=5, freq="h"))
    )
    timezone_issues = validate_timezone_awareness(naive)
    assert timezone_issues[0]["type"] == "timezone"
    assert validate_issue_severity({"type": "schema_validation"}) == "high"
    assert (
        validate_issue_severity({"type": "spread_anomaly", "issue": "negative_spread"})
        == "critical"
    )
    assert validate_issue_remediation_action({"type": "gap"}) == "backfill_or_drop"

    annotated = validate_annotate_issues([{"type": "gap", "count": 2}])
    summary = validate_remediation_summary(annotated)
    assert summary["severity_counts"]["medium"] == 1

    invalid_profile = validate_ohlcv_quality(sample_df(), profile="invalid")
    assert invalid_profile["status"] == "error"

    live = validate_ohlcv_quality(sample_df(), profile="live", expected_frequency="1h")
    assert live["status"] == "success"
    assert live["data"]["decision"]["profile"] == "live"

    minimum = validate_ohlcv_quality(sample_df(), minimum_rows=10)
    assert minimum["status"] == "success"
    assert any(i["type"] == "minimum_history" for i in minimum["data"]["issues_found"])


def test_additional_noop_and_error_branches():
    plain = pd.DataFrame({"x": [1, 2]})
    assert validate_spread(plain) == ({}, [])
    zero_rows, zero_issues = validate_zero_volume(plain)
    flat_rows, flat_issues = validate_flatlines(plain, min_run_length=3)
    assert zero_rows.empty and zero_issues == []
    assert flat_rows.empty and flat_issues == []
    _, no_spikes = validate_spikes(pd.DataFrame({"Close": [1, 1, 1]}))
    assert no_spikes == []

    schema_failure = validate_ohlcv_quality(pd.DataFrame({"time": ["2026-01-01"]}))
    assert schema_failure["status"] == "success"
    assert schema_failure["data"]["summary"]["quality_score"] == 0.0
