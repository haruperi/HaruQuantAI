"""Unit tests for immutable standard response contracts."""

from dataclasses import dataclass

import pytest
from app.utils import (
    ResponseMetadata,
    RiskLevel,
    StandardError,
    StandardResponse,
)
from pydantic import ValidationError as PydanticValidationError

_REQUEST_ID = "req-00000000-0000-4000-8000-000000000001"
_CORRELATION_ID = "cor-00000000-0000-4000-8000-000000000002"


def _metadata(**overrides: object) -> ResponseMetadata:
    """Build valid metadata with optional field overrides."""
    values: dict[str, object] = {
        "name": "data.get_market_data",
        "domain": "data",
        "risk_level": RiskLevel.LOW,
        "request_id": _REQUEST_ID,
        "correlation_id": _CORRELATION_ID,
        "execution_ms": 1.2344,
        "read_only": True,
        "writes_file": False,
        "modifies_database": False,
        "places_trade": False,
        "requires_network": True,
        "extensions": {"provider": "example"},
    }
    values.update(overrides)
    return ResponseMetadata.model_validate(values)


def test_standard_response_has_exact_top_level_shape_and_raw_data() -> None:
    @dataclass(frozen=True)
    class RawResult:
        value: int

    raw = RawResult(value=7)
    response = StandardResponse[RawResult](
        status="success",
        message="Market data retrieved",
        data=raw,
        error=None,
        metadata=_metadata(),
    )

    assert response.data is raw
    assert set(response.model_dump()) == {
        "status",
        "message",
        "data",
        "error",
        "metadata",
    }
    assert not isinstance(response.data, dict)
    assert response.model_dump(mode="json")["data"] == {"value": 7}


def test_success_response_allows_none_data() -> None:
    response = StandardResponse[None](
        status="success",
        message="Disconnected",
        data=None,
        error=None,
        metadata=_metadata(),
    )
    assert response.data is None


def test_error_response_requires_error_and_null_data() -> None:
    error = StandardError(code="VALIDATION_FAILED", details={"field": "symbol"})
    response = StandardResponse[dict[str, str]](
        status="error",
        message="Request validation failed",
        data=None,
        error=error,
        metadata=_metadata(),
    )
    assert response.error is error

    with pytest.raises(PydanticValidationError, match="requires error and data=None"):
        StandardResponse[dict[str, str]](
            status="error",
            message="Request validation failed",
            data={"unexpected": "payload"},
            error=error,
            metadata=_metadata(),
        )


def test_standard_response_rejects_missing_extra_and_invalid_status() -> None:
    complete = {
        "status": "success",
        "message": "Completed",
        "data": None,
        "error": None,
        "metadata": _metadata(),
    }
    for field in complete:
        missing = dict(complete)
        del missing[field]
        with pytest.raises(PydanticValidationError):
            StandardResponse[None].model_validate(missing)
    with pytest.raises(PydanticValidationError):
        StandardResponse[None].model_validate(
            {**complete, "status": "pending"},
        )
    with pytest.raises(PydanticValidationError):
        StandardResponse[None].model_validate(
            {**complete, "unexpected": True},
        )


def test_metadata_requires_all_side_effect_fields_and_rejects_conflicts() -> None:
    dumped = _metadata().model_dump()
    del dumped["writes_file"]
    with pytest.raises(PydanticValidationError):
        ResponseMetadata.model_validate(dumped)

    with pytest.raises(PydanticValidationError, match="read_only"):
        _metadata(writes_file=True)


def test_metadata_extensions_preserve_fields_and_redact_secrets() -> None:
    metadata = _metadata(
        extensions={
            "legacy_status": "blocked",
            "warnings": [{"code": "STALE_EVIDENCE"}],
            "api_token": "do-not-return",
        }
    )
    serialized = metadata.model_dump(mode="json")
    assert serialized["extensions"] == {
        "legacy_status": "blocked",
        "warnings": [{"code": "STALE_EVIDENCE"}],
        "api_token": "[REDACTED]",
    }
    assert metadata.execution_ms == 1.234


def test_standard_error_rejects_malformed_shape_and_redacts_details() -> None:
    error = StandardError(
        code="INTERNAL_ERROR",
        details={"authorization": "Bearer unsafe"},
    )
    assert error.model_dump(mode="json")["details"] == {"authorization": "[REDACTED]"}

    with pytest.raises(PydanticValidationError):
        StandardError.model_validate(
            {
                "code": "INTERNAL_ERROR",
                "details": {},
                "message": "not part of the contract",
            }
        )
    with pytest.raises(PydanticValidationError):
        StandardError(code="not-canonical", details={})
