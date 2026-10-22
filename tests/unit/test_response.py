"""Verify immutable response snapshots, strict JSON export, and UTC metadata."""

from __future__ import annotations

import json
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from app.host.logging import shutdown_logging
from app.host.response import (
    ApiResponse,
    ApiResponseCLI,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)


@pytest.fixture(autouse=True)
def _logging_cleanup() -> Generator[None]:
    """Drain asynchronous telemetry before pytest releases its capture streams."""
    yield
    shutdown_logging()


def test_recursive_json_serialization() -> None:
    """Normalize supported Python values in data, errors, and extensions."""

    @dataclass
    class Payload:
        created: datetime
        source: Path
        tags: set[str]

    payload = Payload(datetime(2026, 1, 1, tzinfo=UTC), Path("audit"), {"b", "a"})
    expected = {
        "created": "2026-01-01T00:00:00+00:00",
        "source": "audit",
        "tags": ["a", "b"],
    }
    result = StandardResponse.success(
        {"payload": payload, "day": date(2026, 1, 2)}, extensions={"payload": payload}
    ).to_dict()
    assert result["data"] == {"payload": expected, "day": "2026-01-02"}
    assert result["metadata"]["extensions"] == {"payload": expected}
    failure = ApiResponse.error("ERROR", "Failed", details={"payload": payload})
    assert failure["error"]["details"] == {"payload": expected}
    json.dumps(result, allow_nan=False)
    json.dumps(failure, allow_nan=False)


def test_snapshots_and_exports_are_isolated() -> None:
    """Source objects and returned objects cannot mutate an existing envelope."""
    source = {"nested": {"items": [1]}}
    response = StandardResponse.success(source, extensions=source)
    error = StandardError("ERROR", "Failed", details=source)
    failure = StandardResponse.failure("Failed", error, data=source, extensions=source)
    source["nested"]["items"].append(2)
    for envelope in (response, failure):
        exported = envelope.to_dict()
        assert exported["data"] == {"nested": {"items": [1]}}
        exported["data"]["nested"]["items"].append(3)
        exported["metadata"]["extensions"]["nested"]["items"].append(3)
        assert envelope.to_dict()["data"]["nested"]["items"] == [1]
        assert envelope.to_dict()["metadata"]["extensions"]["nested"]["items"] == [1]
    fail_export = failure.to_dict()
    fail_export["error"]["details"]["nested"]["items"].append(3)
    assert failure.to_dict()["error"]["details"]["nested"]["items"] == [1]
    value = response.unwrap()
    value["nested"]["items"].append(4)
    assert response.unwrap()["nested"]["items"] == [1]
    with pytest.raises(RuntimeError, match="ERROR"):
        failure.unwrap()


def test_nested_snapshot_mutations_are_rejected() -> None:
    """Frozen dataclasses also protect their nested mapping/sequence contents."""
    response = StandardResponse.success({"items": [1]}, extensions={"items": [1]})
    error = StandardError("ERROR", "Failed", details={"items": [1]})
    assert error.details is not None
    assert response.data is not None
    with pytest.raises(TypeError):
        response.data["new"] = [2]
    with pytest.raises(TypeError):
        response.metadata.extensions["new"] = 2  # type: ignore[index]
    with pytest.raises(TypeError):
        error.details["new"] = 2  # type: ignore[index]
    with pytest.raises(TypeError):
        response.data["items"][0] = 2


def test_direct_constructors_and_shared_children() -> None:
    """Direct construction freezes nested values without rejecting shared DAGs."""
    child = {"items": [1]}
    metadata = ResponseMetadata("2026-01-01T03:00:00+03:00", extensions=child)
    response = StandardResponse("success", "OK", [child, child], None, metadata)
    child["items"].append(2)
    exported = response.to_dict()
    assert exported["data"] == [{"items": [1]}, {"items": [1]}]
    assert exported["metadata"]["extensions"] == {"items": [1]}
    assert exported["metadata"]["timestamp_utc"] == "2026-01-01T00:00:00+00:00"


@pytest.mark.parametrize(
    "value", [object(), {1: "bad key"}, float("nan"), float("inf")]
)
@pytest.mark.parametrize("branch", ["data", "details", "extensions"])
def test_unsupported_values_fail_closed(value: Any, branch: str) -> None:
    """Unsupported and nonfinite values fail before an envelope can be returned."""
    with pytest.raises((TypeError, ValueError)):
        if branch == "data":
            StandardResponse.success({"nested": value})
        elif branch == "details":
            StandardError("ERROR", "Failed", details={"nested": value})
        else:
            ResponseMetadata("2026-01-01T00:00:00Z", extensions={"nested": value})


@pytest.mark.parametrize("kind", ["list", "mapping", "dataclass"])
def test_cycles_fail_with_a_stable_error(kind: str) -> None:
    """Reject cyclic graphs rather than recurse indefinitely or expose contents."""
    value: Any
    if kind == "list":
        value = []
        value.append(value)
    elif kind == "mapping":
        value = {}
        value["self"] = value
    else:

        @dataclass
        class Node:
            child: Any = None

        value = Node()
        value.child = value
    with pytest.raises(ValueError, match=r"[Cc]yclic"):
        StandardResponse.success(value)


def test_set_serialization_is_deterministic() -> None:
    """Both mutable and immutable sets produce canonical JSON array order."""
    one = StandardResponse.success({3, 1, 2}).to_dict()["data"]
    two = StandardResponse.success(frozenset([2, 3, 1])).to_dict()["data"]
    assert one == two == [1, 2, 3]


@pytest.mark.parametrize(
    "duration,error_type",
    [
        (-1, ValueError),
        (float("nan"), ValueError),
        (float("inf"), ValueError),
        (-float("inf"), ValueError),
        (True, TypeError),
        ("2", TypeError),
    ],
)
def test_invalid_durations_are_rejected(
    duration: Any, error_type: type[Exception]
) -> None:
    """Direct metadata and API factories reject bool, text, and invalid numbers."""
    with pytest.raises(error_type, match="duration_ms"):
        ResponseMetadata("2026-01-01T00:00:00Z", duration_ms=duration)
    with pytest.raises(error_type, match="duration_ms"):
        ApiResponse.ok(meta={"duration_ms": duration})


@pytest.mark.parametrize(
    "timestamp", ["", "invalid", "2026-01-01", "2026-01-01T12:00:00"]
)
def test_invalid_timestamps_are_rejected(timestamp: str) -> None:
    """Require a parseable timezone-aware timestamp at all construction paths."""
    with pytest.raises(ValueError, match="timestamp_utc"):
        ResponseMetadata(timestamp)
    with pytest.raises(ValueError, match="timestamp_utc"):
        ApiResponse.ok(meta={"timestamp_utc": timestamp})


@pytest.mark.parametrize("duration", [0, 0.5, None])
def test_valid_metadata(duration: float | None) -> None:
    """Normalize offset timestamps to UTC and preserve finite durations."""
    metadata = ResponseMetadata("2026-01-01T03:00:00+03:00", duration_ms=duration)
    assert metadata.timestamp_utc == "2026-01-01T00:00:00+00:00"
    assert metadata.duration_ms == duration


def test_cli_checks_snapshot_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI verification exercises the strengthened contracts before success."""
    assert ApiResponseCLI.run(["--verify", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "verified"
    assert result["json_safe"] is True
    assert result["snapshot_isolated"] is True


def test_cli_rejects_an_incorrect_snapshot(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verification returns failure when snapshot semantics are broken."""
    monkeypatch.setattr(StandardResponse, "unwrap", lambda _: {})
    assert ApiResponseCLI.run(["--verify", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "failed"


def test_dataclass_source_is_detached() -> None:
    """Retaining and mutating the source dataclass cannot change the snapshot."""

    @dataclass
    class Source:
        tags: set[str]

    source = Source({"before"})
    response = StandardResponse.success(source)
    source.tags.add("after")
    assert response.to_dict()["data"] == {"tags": ["before"]}


def test_duration_overflow_is_rejected() -> None:
    """An enormous integer duration fails with the same stable validation error."""
    with pytest.raises(ValueError, match="duration_ms"):
        ResponseMetadata("2026-01-01T00:00:00Z", duration_ms=10**400)
