"""Tests for StandardResponse envelope and host response builders."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from typing import Any

import pytest
from app.core.lib.responses import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
    build_typed_response,
)


def _make_metadata() -> ResponseMetadata:
    return ResponseMetadata(operation="test", duration_ms=1.5)


def test_empty_response() -> None:
    payload: dict[str, list[Any]] = {"items": []}
    resp = StandardResponse(request_id="req-001", data=payload)
    assert (
        resp.to_json()
        == b'{"request_id":"req-001","data":{"items":[]},"revision":null}'
    )


def test_response_revision() -> None:
    resp = StandardResponse(request_id="req-002", data=False, revision=0)
    assert resp.data is False
    assert resp.revision == 0
    assert resp.to_dict() == {
        "request_id": "req-002",
        "data": False,
        "revision": 0,
    }

    for invalid_rev in [True, -1, "1"]:
        with pytest.raises(
            ValueError, match="revision must be a non-negative integer or None"
        ):
            StandardResponse(request_id="req-002", data=False, revision=invalid_rev)  # type: ignore[arg-type]


def test_response_detached_and_unicode() -> None:
    source: dict[str, Any] = {"items": ["a"]}
    resp = StandardResponse(request_id="req-003", data=source)
    source["items"].append("b")
    assert resp.to_dict()["data"] == {"items": ["a"]}

    d = resp.to_dict()
    assert isinstance(d["data"], dict)
    assert isinstance(d["data"]["items"], list)
    d["data"]["items"].append("c")
    assert resp.to_dict()["data"] == {"items": ["a"]}
    assert (
        resp.to_json()
        == b'{"request_id":"req-003","data":{"items":["a"]},"revision":null}'
    )

    unicode_resp = StandardResponse(request_id="req-u", data="\ud83d")
    assert (
        unicode_resp.to_json()
        == b'{"request_id":"req-u","data":"\\ud83d","revision":null}'
    )

    with pytest.raises(ValueError, match="value must contain finite JSON values"):
        StandardResponse(request_id="req-nan", data=float("nan"))


def test_build_typed_response() -> None:
    resp = build_typed_response(
        request_id="req-typed",
        data=[1, 2, 3],
        json_payload=[1, 2, 3],
        revision=1,
    )
    assert resp.request_id == "req-typed"
    assert resp.data == [1, 2, 3]
    assert resp.revision == 1


def test_success_returns_json_dictionary() -> None:
    data = {"created": datetime(2026, 10, 23, tzinfo=UTC)}
    result = StandardResponse.success(
        message="Done", data=data, metadata=_make_metadata()
    )
    assert isinstance(result, dict)
    assert result["data"]["created"] == "2026-10-23T00:00:00Z"
    assert result["success"] is True
    assert "status" not in result
    assert result["error"] is None
    assert result["metadata"]["side_effects"] == []
    json.dumps(result, allow_nan=False)
    result["data"]["created"] = "changed"
    assert isinstance(data["created"], datetime)


def test_error_and_metadata_are_deeply_frozen_and_output_is_detached() -> None:
    source = {"nested": [{"value": 1}]}
    error = StandardError(code=ErrorCode.CONFLICT, message="Conflict", details=source)
    context = ResponseMetadata(
        operation="save",
        duration_ms=2,
        extensions=source,
        side_effects=("Created temporary file",),
    )
    source["nested"][0]["value"] = 2
    assert error.details["nested"][0]["value"] == 1
    with pytest.raises(TypeError):
        context.extensions["nested"][0]["value"] = 3
    result = StandardResponse.failure(
        message="Save failed", error=error, metadata=context
    )
    with pytest.raises(FrozenInstanceError):
        error.message = "Changed"  # type: ignore[misc]
    assert result["success"] is False
    assert result["error"]["code"] == "conflict"
    result["metadata"]["extensions"]["nested"][0]["value"] = 4
    assert context.extensions["nested"][0]["value"] == 1
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("message", [" ", "x" * 1025])
@pytest.mark.parametrize(
    "builder", [StandardResponse.success, StandardResponse.failure]
)
def test_invalid_messages(builder: Any, message: str) -> None:
    kwargs: dict[str, Any] = {"message": message, "metadata": _make_metadata()}
    if builder is StandardResponse.failure:
        kwargs["error"] = StandardError(code=ErrorCode.INTERNAL, message="Failed")
    with pytest.raises(ValueError):
        builder(**kwargs)


def test_invalid_builder_arguments() -> None:
    error = StandardError(code=ErrorCode.INTERNAL, message="Failed")
    with pytest.raises(TypeError):
        StandardResponse.failure(
            message="Failed",
            metadata=_make_metadata(),
            error=None,  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError):
        StandardResponse.failure(message="Failed", metadata=_make_metadata())  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        StandardResponse.failure(
            message="Failed",
            metadata=_make_metadata(),
            error=error,
            data=1,  # type: ignore[call-arg]
        )
    with pytest.raises(TypeError):
        StandardResponse.success(
            message="Done",
            metadata=_make_metadata(),
            error=error,  # type: ignore[call-arg]
        )
    with pytest.raises(TypeError):
        StandardResponse.success(message="Done", metadata=None)  # type: ignore[arg-type]


@pytest.mark.parametrize("duration", [-1, float("nan"), float("inf"), True])
def test_invalid_execution_duration(duration: Any) -> None:
    with pytest.raises(ValueError):
        ResponseMetadata(operation="test", duration_ms=duration)


@pytest.mark.parametrize("value", [object(), float("nan"), {1: "invalid key"}])
def test_non_json_extensions_rejected(value: Any) -> None:
    with pytest.raises(ValueError):
        ResponseMetadata(operation="test", duration_ms=0, extensions={"bad": value})


def test_successful_none_result_is_valid() -> None:
    result = StandardResponse.success(message="Done", metadata=_make_metadata())
    assert result["data"] is None
