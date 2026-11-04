"""Executable donor vectors, host aliases and isolated registry persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest
from app.core.data import io, timeframes
from app.core.data.charts import ChartDef
from app.core.data.timeframes import TimeframeManager
from app.core.enums import Timeframe
from app.core.lib.errors import DomainError

VECTORS: list[dict[str, Any]] = [
    json.loads(line)
    for line in (Path(__file__).parent / "fixtures/s15/vectors.jsonl")
    .read_text(encoding="utf-8-sig")
    .splitlines()
]


@pytest.mark.parametrize("vector", [v for v in VECTORS if v["kind"] != "string"])
def test_java_vectors(vector: dict[str, Any]) -> None:
    value = vector["input"]
    if vector["kind"] == "name":
        assert timeframes.get_tf_name(value) == vector["value"]
    elif vector["kind"] == "legacy":
        assert timeframes.translate_sq3_tf_to_string(value) == vector["value"]
    else:
        assert TimeframeManager.is_valid(value) == vector["valid"]
        assert timeframes.comparator_seconds_count(value) == vector["seconds"]
        assert timeframes.translate_to_mt_constant(value) == vector["mt"]
        for field, function in (
            ("millis", timeframes.get_millis),
            ("hash", timeframes.get_tf_hash),
        ):
            if vector[field] == "error":
                with pytest.raises(DomainError, match="timeframe"):
                    function(value)
            else:
                assert function(value) == vector[field]


@pytest.mark.parametrize(
    "value,seconds",
    [
        ("TICK", 0),
        ("ticks", 0),
        ("Intraday", 0),
        ("CURRENT", 0),
        ("H7", 25200),
        ("D2", 172800),
        ("Weekly", 604800),
        ("Monthly", 2419200),
        ("1MIN", 60),
        ("60M", 3600),
        ("1W", 604800),
        ("MN1", 2419200),
        ("H+2", 7200),
        ("M-1", -60),
        ("S0", 0),
    ],
)
def test_shared_duration_owner(value: str, seconds: int) -> None:
    assert timeframes.timeframe_to_seconds(value) == seconds
    assert ChartDef("EURUSD", timeframe=value).timeframe_seconds() == seconds


def test_enum_durations_and_old_owner_removed() -> None:
    assert not hasattr(io, "timeframe_to_seconds")
    for value in Timeframe:
        assert value.to_seconds() == timeframes.timeframe_to_seconds(value.value)
        assert value.to_minutes() == value.to_seconds() // 60
    # Broker enum remains finite; custom periods use the shared string contract.
    with pytest.raises(ValueError):
        Timeframe.from_string("H7")


def test_minute_names_and_donor_comparison() -> None:
    assert timeframes.minute_timeframe(14) == timeframes.translate_sq3_tf_to_string(14)
    assert timeframes.is_timeframe_less_than("H7", "D2")
    assert not timeframes.is_timeframe_less_than("M60", "H1")
    assert timeframes.is_timeframe_less_than("M-1", "TICK")
    with pytest.raises(ValueError):
        timeframes.minute_timeframe(2**31)


def test_registry_defaults_custom_order_and_restart(tmp_path: Path) -> None:
    path = tmp_path / "customTimeframes.txt"
    path.write_bytes(b"H7\r\n\r\nM3\r\nH7")
    manager = TimeframeManager(path)
    assert manager.get_timeframes().count("H7") == 1
    assert manager.tf_exists("H7")
    assert not manager.tf_exists("h7")
    assert "H2" in manager.get_predefined_timeframes()
    assert not manager.tf_exists("H2")
    manager.add_timeframe("D2")
    assert path.read_bytes() == b"H7\r\nM3\r\nD2"
    assert TimeframeManager(path).get_timeframes() == manager.get_timeframes()
    assert manager.get_timeframes().index("H7") < manager.get_timeframes().index("D2")
    detached = manager.get_predefined_timeframes()
    detached.clear()
    assert manager.get_predefined_timeframes()
    for value in ("H7", "TICK", "Intraday", "garbage"):
        with pytest.raises(ValueError):
            manager.add_timeframe(value)


def test_registry_failures_preserve_disk_and_memory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "customTimeframes.txt"
    path.write_bytes(b"H7")
    manager = TimeframeManager(path)

    def reject_replace(*args: object) -> None:
        raise OSError("isolated replacement failure")

    monkeypatch.setattr(Path, "replace", reject_replace)
    with pytest.raises(OSError, match="replacement failure"):
        manager.add_timeframe("D2")
    assert not manager.tf_exists("D2")
    assert path.read_bytes() == b"H7"
    assert list(tmp_path.iterdir()) == [path]
    with pytest.raises(ValueError, match="explicit"):
        TimeframeManager().add_timeframe("H7")
    with pytest.raises(OSError):
        TimeframeManager(tmp_path).get_timeframes()


def test_comparator_error_sentinel_and_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG):
        assert sorted(
            ["Monthly", "invalid", "M1", "Intraday", "TICK"],
            key=timeframes.timeframe_sort_key,
        ) == [
            "Intraday",
            "TICK",
            "M1",
            "invalid",
            "Monthly",
        ]
        assert timeframes.comparator_seconds_count(None) == 2**31 - 1
        assert not TimeframeManager.is_valid(None)
        TimeframeManager().get_timeframes()
    messages = " ".join(record.message for record in caplog.records)
    for requirement in ("conversion", "registry", "ordering"):
        assert f"FR-data-timeframe-{requirement}" in messages
