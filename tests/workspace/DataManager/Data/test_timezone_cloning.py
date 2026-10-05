"""Verify timezone cloning boundaries and explicit semantics."""

from dataclasses import replace
from datetime import datetime
from typing import Any, cast

from app.workspace.DataManager.Data.contracts import Catalog, TickRecord
from app.workspace.DataManager.Data.timezone_cloning import clone_timezone


def ms(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp() * 1000)


def test_named_zone_preserves_instants_at_dst_transitions(dataset):
    times = (
        ms("2024-03-10T06:59:00+00:00"),
        ms("2024-03-10T07:00:00+00:00"),
        ms("2024-11-03T05:30:00+00:00"),
        ms("2024-11-03T06:30:00+00:00"),
    )
    source = replace(
        dataset, timeframe="TICK", records=tuple(TickRecord(t, 1, 2) for t in times)
    )
    clone = clone_timezone(
        Catalog((source,)),
        "fx",
        clone_id="clone",
        symbol="CLONE",
        target_timezone="America/New_York",
    ).unwrap()
    assert clone.records == source.records and clone.parent_id == "fx"
    assert clone.timezone == "America/New_York"


def test_target_local_weekend_and_fixed_shift(dataset):
    source = replace(
        dataset,
        timeframe="TICK",
        records=(
            TickRecord(ms("2024-01-05T20:00:00+00:00"), 1, 2),
            TickRecord(ms("2024-01-07T20:00:00+00:00"), 1, 2),
        ),
    )
    catalog = Catalog((source,))
    clone = clone_timezone(
        catalog,
        "fx",
        clone_id="c",
        symbol="C",
        target_timezone="Asia/Kolkata",
        remove_weekends=True,
    ).unwrap()
    assert clone.records == (source.records[1],)
    shifted = clone_timezone(
        catalog, "fx", clone_id="c", symbol="C", shift_hours=5
    ).unwrap()
    assert shifted.records[0].time_ms == source.records[0].time_ms + 18_000_000
    assert shifted.timezone == source.timezone
    assert (
        clone_timezone(catalog, "fx", clone_id="c", symbol="C", shift_hours=0)
        .unwrap()
        .records
        == source.records
    )


def test_invalid_clone_options_and_identity(catalog, dataset):
    base: dict[str, Any] = {"clone_id": "c", "symbol": "C"}
    assert (
        clone_timezone(catalog, "missing", target_timezone="UTC", **base).error_code
        == "UNKNOWN_DATASET"
    )
    assert (
        clone_timezone(catalog, "fx", **base).error_code == "AMBIGUOUS_TIMEZONE_OPTIONS"
    )
    assert clone_timezone(
        catalog, "fx", target_timezone="UTC", shift_hours=1, **base
    ).is_error
    for hours in [24, -24, True]:
        assert (
            clone_timezone(catalog, "fx", shift_hours=hours, **base).error_code
            == "INVALID_SHIFT"
        )
    assert (
        clone_timezone(catalog, "fx", target_timezone="EETUS", **base).error_code
        == "UNSUPPORTED_TIMEZONE"
    )
    assert (
        clone_timezone(
            catalog, "fx", target_timezone="UTC", remove_weekends=cast("Any", 1), **base
        ).error_code
        == "INVALID_WEEKEND_OPTION"
    )
    assert (
        clone_timezone(
            catalog, "fx", clone_id="fx", symbol="C", target_timezone="UTC"
        ).error_code
        == "INVALID_CLONE"
    )
    assert clone_timezone(
        catalog, "fx", clone_id="c", symbol="AAPL", target_timezone="UTC"
    ).is_error
    assert clone_timezone(
        catalog, "fx", clone_id="c", symbol="bad name", target_timezone="UTC"
    ).is_error
    limited = Catalog((replace(dataset, restricted=True),))
    assert (
        clone_timezone(limited, "fx", target_timezone="UTC", **base).error_code
        == "CLONE_NOT_ALLOWED"
    )
    clone = replace(dataset, id="clone", symbol="CLONE", parent_id="fx")
    assert (
        clone_timezone(
            Catalog((dataset, clone)), "clone", target_timezone="UTC", **base
        ).error_code
        == "CLONE_NOT_ALLOWED"
    )


def test_host_timezone_environment_cannot_change_output(catalog, monkeypatch):
    results = []
    for zone in ["UTC", "America/Los_Angeles", "Asia/Kolkata"]:
        monkeypatch.setenv("TZ", zone)
        results.append(
            clone_timezone(
                catalog,
                "fx",
                clone_id="c",
                symbol="C",
                target_timezone="America/New_York",
            ).unwrap()
        )
    assert results[0] == results[1] == results[2]


def test_shift_bounds_and_duplicate_order(dataset):
    source = replace(
        dataset, timeframe="TICK", records=(TickRecord(0, 1, 2), TickRecord(0, 2, 3))
    )
    catalog = Catalog((source,))
    clone = clone_timezone(
        catalog, "fx", clone_id="c", symbol="C", shift_hours=-23
    ).unwrap()
    assert clone.records == (
        TickRecord(-82_800_000, 1, 2),
        TickRecord(-82_800_000, 2, 3),
    )
    edge = replace(source, records=(TickRecord(253_402_300_799_999, 1, 2),))
    assert (
        clone_timezone(
            Catalog((edge,)), "fx", clone_id="c", symbol="C", shift_hours=1
        ).error_code
        == "INVALID_CLONE"
    )
