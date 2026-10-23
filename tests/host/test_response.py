import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)


def metadata():
    return ResponseMetadata(operation="test", duration_ms=1.5)


def test_success_returns_json_dictionary():
    data = {"created": datetime(2026, 10, 23, tzinfo=UTC)}
    result = StandardResponse.success(message="Done", data=data, metadata=metadata())
    assert isinstance(result, dict)
    assert result["data"]["created"] == "2026-10-23T00:00:00Z"
    assert result["success"] is True
    assert "status" not in result
    assert result["error"] is None
    assert result["metadata"]["side_effects"] == []
    json.dumps(result, allow_nan=False)
    result["data"]["created"] = "changed"
    assert isinstance(data["created"], datetime)


def test_error_and_metadata_are_deeply_frozen_and_output_is_detached():
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
        error.message = "Changed"
    assert result["success"] is False
    assert result["error"]["code"] == "conflict"
    result["metadata"]["extensions"]["nested"][0]["value"] = 4
    assert context.extensions["nested"][0]["value"] == 1
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("message", [" ", "x" * 1025])
@pytest.mark.parametrize(
    "builder", [StandardResponse.success, StandardResponse.failure]
)
def test_invalid_messages(builder, message):
    kwargs = {"message": message, "metadata": metadata()}
    if builder is StandardResponse.failure:
        kwargs["error"] = StandardError(code=ErrorCode.INTERNAL, message="Failed")
    with pytest.raises(ValueError):
        builder(**kwargs)


def test_invalid_builder_arguments():
    error = StandardError(code=ErrorCode.INTERNAL, message="Failed")
    with pytest.raises(TypeError):
        StandardResponse.failure(message="Failed", metadata=metadata(), error=None)
    with pytest.raises(TypeError):
        StandardResponse.failure(message="Failed", metadata=metadata())
    with pytest.raises(TypeError):
        StandardResponse.failure(
            message="Failed", metadata=metadata(), error=error, data=1
        )
    with pytest.raises(TypeError):
        StandardResponse.success(message="Done", metadata=metadata(), error=error)
    with pytest.raises(TypeError):
        StandardResponse.success(message="Done", metadata=None)


@pytest.mark.parametrize("duration", [-1, float("nan"), float("inf"), True])
def test_invalid_execution_duration(duration):
    with pytest.raises(ValueError):
        ResponseMetadata(operation="test", duration_ms=duration)


@pytest.mark.parametrize("value", [object(), float("nan"), {1: "invalid key"}])
def test_non_json_extensions_rejected(value):
    with pytest.raises(ValueError):
        ResponseMetadata(operation="test", duration_ms=0, extensions={"bad": value})


def test_successful_none_result_is_valid():
    result = StandardResponse.success(message="Done", metadata=metadata())
    assert result["data"] is None
