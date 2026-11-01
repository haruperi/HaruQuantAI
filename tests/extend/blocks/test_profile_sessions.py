"""Donor-derived numerical qualification plus causal session boundary regressions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pytest
from app.extend.blocks.indicators.volume.tpo_profile import TPOProfile
from app.extend.blocks.indicators.volume.volume_profile import VolumeProfile
from app.extend.blocks.series import BarData
from app.include.calculators.profile import TPO_OUTPUTS, VOLUME_OUTPUTS
from app.include.calculators.profile_sessions import session_bounds
from pydantic import ValidationError

REFERENCE = json.loads(
    Path("docs/dev/fixtures/profile-donor-reference.json").read_text()
)
for reference_case in REFERENCE["cases"] + REFERENCE["sessions"]:
    reference_case["data"] = REFERENCE["datasets"][reference_case["dataset"]]


def context(rows, *, terminal=True):
    data = np.asarray(rows, dtype=float)
    if terminal:
        last = data[-1].copy()
        last[0] = 1704153600000
        data = np.vstack((data, last))
    return BarData.from_arrays(
        **dict(
            zip(
                ("timestamps", "open", "high", "low", "close", "volume"),
                data.T,
                strict=True,
            )
        )
    )


@pytest.mark.parametrize("case", REFERENCE["cases"], ids=lambda case: case["id"])
def test_profiles_against_executed_donor_java(case):
    """Reference values come from unmodified Java method bodies, not Python."""
    settings = {
        "session_type": 1,
        "timestamp_unit": "milliseconds",
        "profile_rows": 10,
        "bin_size_mode": case["bin_size_mode"],
        "ticks_per_bin": 1,
        "tick_size": 0.25,
    }
    settings.update(case.get("configuration", {}))
    if case["kind"] == "VP":
        indicator = VolumeProfile(
            **settings,
            enable_lvn=True,
            enable_vcp=case["enable_vcp"],
            cluster_spread=1.5,
        )
    else:
        indicator = TPOProfile(**settings)
    result = indicator.calculate(context(case["data"]))
    for name, expected in case["expected"].items():
        assert result[name].values[-1] == pytest.approx(
            expected, rel=2e-14, abs=1e-12
        ), name


@pytest.mark.parametrize("case", REFERENCE["sessions"], ids=lambda case: case["id"])
def test_session_replay_against_executed_donor_on_bar_update(case):
    """Qualify every calendar mode and all swing reversal methods bar by bar."""
    settings = {
        "session_type": case["session_type"],
        "timestamp_unit": "milliseconds",
        "bin_size_mode": 1,
        "profile_rows": 10,
        "tick_size": 0.25,
    }
    settings.update(case.get("configuration", {}))
    indicator = (
        VolumeProfile(
            **settings,
            pivot_method=case["pivot_method"],
            enable_lvn=True,
            cluster_spread=1.5,
        )
        if case["kind"] == "VP"
        else TPOProfile(**settings)
    )
    result = indicator.calculate(context(case["data"], terminal=False))
    if case["session_type"] >= 9:
        assert any(row["poc"] != 0 for row in case["expected"])
    for index, expected in enumerate(case["expected"]):
        for name, value in expected.items():
            # Explicitly corrected donor cross-session previous-POC contamination.
            if case.get("configuration", {}).get(
                "profile_mode"
            ) == "multi" and name in ("delta_poc", "delta_va"):
                continue
            assert result[name].values[index] == pytest.approx(
                value, rel=2e-14, abs=1e-12
            ), (index, name)


def test_named_session_deltas_are_isolated_instead_of_copying_donor_contamination():
    case = next(row for row in REFERENCE["sessions"] if row["id"] == "VP_multi_True_15")
    bars = context(case["data"], terminal=False)
    settings = {
        "bin_size_mode": 1,
        "profile_rows": 10,
        "timestamp_unit": "milliseconds",
        "enable_lvn": True,
        "cluster_spread": 1.5,
    }
    multi = VolumeProfile(**settings, **case["configuration"]).calculate(bars)
    london = VolumeProfile(
        **settings,
        profile_mode="multi",
        session_mode=2,
        enable_new_york=False,
        enable_sydney=False,
        enable_tokyo=False,
    ).calculate(bars)
    for key in ("delta_poc", "delta_va"):
        # Both stay equal to the first enabled session's own previous calculation.
        np.testing.assert_array_equal(multi[key].values, london[key].values)
    assert any(
        abs(multi["delta_poc"].values[i] - row["delta_poc"]) > 1e-10
        for i, row in enumerate(case["expected"])
    )


def epoch(text):
    return int(datetime.fromisoformat(text).replace(tzinfo=UTC).timestamp())


def simple_bars(times):
    n = len(times)
    return BarData.from_arrays(
        timestamps=times,
        open=np.full(n, 101.0),
        high=np.full(n, 104.0),
        low=np.full(n, 100.0),
        close=np.full(n, 102.0),
        volume=np.arange(1.0, n + 1.0),
    )


def test_actual_excludes_current_bar_previous_waits_for_close_and_retains_flat_session():
    times = [
        epoch(t)
        for t in (
            "2024-01-01T00:00",
            "2024-01-01T00:30",
            "2024-01-01T01:00",
            "2024-01-02T00:00",
        )
    ]
    bars = simple_bars(times)
    actual = VolumeProfile(session_type=5, bin_size_mode=1).calculate(bars)
    previous = VolumeProfile(session_type=1, bin_size_mode=1).calculate(bars)
    np.testing.assert_array_equal(actual["total_volume"].values, [0.0, 1.0, 3.0, 3.0])
    np.testing.assert_array_equal(previous["total_volume"].values, [0.0, 0.0, 0.0, 6.0])
    assert actual["ibh"].values[2] == 104.0


@pytest.mark.parametrize(
    "kind,now,start,end",
    [
        (2, "2024-01-03T12:00", "2024-01-01T00:00", "2024-01-08T00:00"),
        (3, "2024-02-29T12:00", "2024-02-01T00:00", "2024-03-01T00:00"),
        (4, "2024-12-31T12:00", "2024-01-01T00:00", "2025-01-01T00:00"),
        (1, "2024-01-07T12:00", "2024-01-05T00:00", "2024-01-06T00:00"),
    ],
)
def test_calendar_bounds(kind, now, start, end):
    assert session_bounds(epoch(now) * 1000, kind, ZoneInfo("UTC")) == (
        epoch(start) * 1000,
        epoch(end) * 1000,
    )


def test_overnight_custom_sessions_exclude_gap_bars_and_named_sessions_are_independent():
    times = [
        epoch(t)
        for t in (
            "2024-01-01T21:00",
            "2024-01-01T22:00",
            "2024-01-02T05:00",
            "2024-01-02T06:00",
            "2024-01-02T12:00",
            "2024-01-02T21:00",
            "2024-01-03T06:00",
        )
    ]
    bars = simple_bars(times)
    custom = VolumeProfile(
        profile_mode="custom", session_start=1260, session_end=360, bin_size_mode=1
    ).calculate(bars)
    np.testing.assert_array_equal(custom["total_volume"].values, [0, 0, 0, 6, 6, 6, 6])
    multi = VolumeProfile(
        profile_mode="multi",
        bin_size_mode=1,
        enable_london=False,
        enable_new_york=False,
        enable_tokyo=False,
        enable_sydney=True,
    ).calculate(bars)
    np.testing.assert_array_equal(multi["poc"].values, multi["sydney_poc"].values)
    assert not multi["london_poc"].values.any()
    assert multi["total_volume"].values[-1] == 6.0


def test_tpo_counts_distinct_brackets_not_bars_and_splits_spanning_bars():
    bars = simple_bars(
        [
            epoch("2024-01-01T00:00"),
            epoch("2024-01-01T00:05"),
            epoch("2024-01-01T00:10"),
            epoch("2024-01-01T01:00"),
        ]
    )
    result = TPOProfile(session_type=5, bin_size_mode=1, profile_rows=10).calculate(
        bars
    )
    # At 00:10 all prices have one letter despite two touching bars.
    assert result["single_prints"].values[2] == 10
    # By 01:00 the 00:10 bar spans the next bracket; there are no single prints.
    assert result["single_prints"].values[3] == 0
    assert result["poor_high"].values[3] == 1
    assert result["excess_high"].values[2] == 1


@pytest.mark.parametrize(
    "indicator",
    [
        VolumeProfile(session_type=1, bin_size_mode=1),
        VolumeProfile(session_type=5, bin_size_mode=1),
        VolumeProfile(session_type=9, bin_size_mode=1),
        VolumeProfile(session_type=10, bin_size_mode=1),
        VolumeProfile(profile_mode="multi", session_mode=2, bin_size_mode=1),
        TPOProfile(session_type=1, bin_size_mode=1),
        TPOProfile(session_type=5, bin_size_mode=1),
    ],
)
def test_all_outputs_are_prefix_causal(indicator):
    case = REFERENCE["cases"][0]
    bars = context(case["data"])
    indicator = indicator.model_copy(update={"timestamp_unit": "milliseconds"})
    full = indicator.calculate(bars)
    assert set(full) == {port.name for port in indicator.spec.outputs}
    for n in (1, 9, 23, 48):
        shorter = context(case["data"][:n], terminal=False)
        prefix = indicator.calculate(shorter)
        for name, value in full.items():
            np.testing.assert_array_equal(value.values[:n], prefix[name].values)


def test_missing_data_invalid_configuration_and_no_rolling_aliases():
    bars = simple_bars([1704067200, 1704070800])
    with pytest.raises(ValueError, match="tick_size"):
        VolumeProfile().calculate(bars)
    with pytest.raises(ValueError, match="timestamps"):
        TPOProfile(bin_size_mode=1).calculate(
            BarData.from_arrays(
                open=[1.0], high=[2.0], low=[1.0], close=[1.0], volume=[1.0]
            )
        )
    with pytest.raises(ValueError, match="open"):
        VolumeProfile(bin_size_mode=1).calculate(
            BarData.from_arrays(
                high=[2.0],
                low=[1.0],
                close=[1.0],
                volume=[1.0],
                timestamps=[1704067200],
            )
        )
    for cls in (VolumeProfile, TPOProfile):
        with pytest.raises(ValidationError):
            cls(period=50)
        with pytest.raises(ValidationError):
            cls(timezone="unknown/zone")
    assert len(VOLUME_OUTPUTS) == 29
    assert len(TPO_OUTPUTS) == 23
