"""Unit tests for standard response factories."""

import asyncio
import time
from dataclasses import dataclass
from types import MappingProxyType

import pytest
from app.utils import (
    COMMON_ERROR_CATALOG,
    ResponseMetadata,
    RiskLevel,
    ValidationError,
    build_response_metadata,
    error_response,
    exception_response,
    success_response,
)

_REQUEST_ID = "req-00000000-0000-4000-8000-000000000001"


def _metadata() -> ResponseMetadata:
    """Build valid metadata using the official monotonic timing helper."""
    return build_response_metadata(
        name="utils.example",
        domain="utils",
        risk_level=RiskLevel.NONE,
        request_id=_REQUEST_ID,
        start_time=time.perf_counter_ns(),
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
        extensions={"legacy_field": "preserved"},
    )


def test_success_factory_keeps_raw_result_without_embedding() -> None:
    @dataclass(frozen=True)
    class RawResult:
        value: int

    raw = RawResult(value=11)
    response = success_response(raw, message="Completed", metadata=_metadata())

    assert response.data is raw
    assert response.metadata.extensions["legacy_field"] == "preserved"


def test_success_factory_serializes_mapping_proxy_without_replacing_raw_data() -> None:
    @dataclass(frozen=True)
    class RawResult:
        value: int

    raw = MappingProxyType({"provider": RawResult(value=17)})
    response = success_response(
        raw,
        message="Catalogue retrieved",
        metadata=_metadata(),
    )

    assert response.data is raw
    with pytest.raises(TypeError):
        response.data["provider"] = RawResult(value=18)
    assert response.model_dump(mode="json")["data"] == {"provider": {"value": 17}}


def test_error_factory_requires_approved_error_code() -> None:
    response = error_response(
        code="VALIDATION_FAILED",
        details={"field": "name"},
        message="Validation failed",
        metadata=_metadata(),
        catalog=COMMON_ERROR_CATALOG,
    )
    assert response.status == "error"
    assert response.data is None
    assert response.error is not None
    assert response.error.code == "VALIDATION_FAILED"

    with pytest.raises(ValidationError) as error:
        error_response(
            code="UNAPPROVED_ERROR",
            details={},
            message="Rejected",
            metadata=_metadata(),
            catalog=COMMON_ERROR_CATALOG,
        )
    assert error.value.code == "ERROR_CODE_UNAPPROVED"


def test_exception_factory_preserves_approved_code_and_hides_unknown_text() -> None:
    known = exception_response(
        ValidationError("VALIDATION_FAILED", "FIELD_MISSING"),
        message="Validation failed",
        metadata=_metadata(),
        catalog=COMMON_ERROR_CATALOG,
    )
    assert known.error is not None
    assert known.error.model_dump(mode="json") == {
        "code": "VALIDATION_FAILED",
        "details": {"detail": "FIELD_MISSING"},
    }

    unknown = exception_response(
        RuntimeError("password=unsafe"),
        message="Unexpected failure",
        metadata=_metadata(),
        catalog=COMMON_ERROR_CATALOG,
    )
    assert unknown.error is not None
    assert unknown.error.model_dump(mode="json") == {
        "code": "INTERNAL_ERROR",
        "details": {"detail": "UNEXPECTED_EXCEPTION"},
    }


@pytest.mark.parametrize(
    "exception",
    [
        asyncio.CancelledError(),
        GeneratorExit(),
        KeyboardInterrupt(),
        SystemExit(),
    ],
)
def test_exception_factory_propagates_process_control(
    exception: BaseException,
) -> None:
    with pytest.raises(type(exception)):
        exception_response(
            exception,
            message="Not converted",
            metadata=_metadata(),
            catalog=COMMON_ERROR_CATALOG,
        )
