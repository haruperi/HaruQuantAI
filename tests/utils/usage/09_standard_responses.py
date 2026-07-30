"""Executable standard-response examples."""

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    build_response_metadata,
    error_response,
    exception_response,
    generate_id,
    get_common_error_catalog,
    get_execution_ms,
    get_standard_response_type,
    success_response,
)


@dataclass(frozen=True, slots=True)
class ExampleResult:
    """Raw result used to demonstrate direct data preservation."""

    value: int


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _metadata() -> Any:
    """Build bounded example response metadata."""
    return build_response_metadata(
        name="utils.standard_response_example",
        domain="utils",
        risk_level="none",
        request_id=generate_id("req"),
        start_time=time.perf_counter_ns(),
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
        extensions={
            "legacy_status": "completed",
            "legacy_warning_count": 0,
        },
    )


def fr_utils_042_through_047_standard_response() -> None:
    """FR-UTL-042..047: Stage 1 & 2 — Build success and error response branches."""
    _header(
        "Stage 1 & 2: Response Construction - Success & Error Envelopes (FR-UTL-042..047)"
    )

    # 1. Success response
    result = ExampleResult(value=42)
    success = success_response(
        result,
        message="Example completed",
        metadata=_metadata(),
    )
    assert success.data is result
    assert success.metadata.extensions["legacy_status"] == "completed"
    assert isinstance(success, get_standard_response_type())
    print(_format_result(success))
    print(f"Data -> success_status='{success.status}', raw_data={success.data}")

    # 2. Error response
    failure = error_response(
        code="VALIDATION_FAILED",
        details={"field": "value"},
        message="Example validation failed",
        metadata=_metadata(),
        catalog=get_common_error_catalog(),
    )
    assert failure.data is None
    assert failure.error is not None
    print(_format_result(failure))
    print(f"Data -> error_status='{failure.status}', error_code='{failure.error.code}'")

    # 3. Exception response
    unexpected = exception_response(
        RuntimeError("secret=must-not-escape"),
        message="Example failed safely",
        metadata=_metadata(),
        catalog=get_common_error_catalog(),
    )
    assert unexpected.error is not None
    assert unexpected.error.code == "INTERNAL_ERROR"
    assert "must-not-escape" not in str(unexpected.model_dump(mode="json"))
    print(_format_result(unexpected))
    print(
        f"Data -> exception_status='{unexpected.status}', code='{unexpected.error.code}'"
    )

    # 4. Timing metadata calculation
    elapsed_ms = get_execution_ms(1_000_000, clock=lambda: 2_234_567)
    assert elapsed_ms == 1.235
    print(_format_result(elapsed_ms))
    print(f"Data -> execution_duration_ms={elapsed_ms}")


def fr_utils_050_immutable_mapping_data() -> None:
    """FR-UTL-050: Stage 3 — Preserve immutable mapping data through JSON serialization."""
    _header(
        "Stage 3: Validated Output Envelope - Immutable Mapping Proxy Response (FR-UTL-050)"
    )
    immutable_data = MappingProxyType({"example": ExampleResult(value=42)})
    immutable_success = success_response(
        immutable_data,
        message="Immutable example completed",
        metadata=_metadata(),
    )
    assert immutable_success.data is immutable_data
    dump = immutable_success.model_dump(mode="json")
    assert dump["data"] == {"example": {"value": 42}}
    print(_format_result(immutable_success))
    print(
        f"Data -> immutable_mapping_keys={list(immutable_success.data.keys())}, json_dump={dump['data']}"
    )


def main() -> None:
    """Run all standard-response examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-UTIL-08 — responses/ — Standard Operation Responses\n\n"
        "Purpose: Define the single business-neutral response contract used by every public operation.\n\n"
        "Module flow:\n"
        "-> raw operation result or caught failure + static operation facts + monotonic start\n"
        "-> validation / factory handling\n"
        "-> validated StandardResponse[T]"
    )

    # Stage 1 & 2: Raw result / failure + factory handling
    fr_utils_042_through_047_standard_response()

    # Stage 3: Validated StandardResponse[T] output
    fr_utils_050_immutable_mapping_data()


if __name__ == "__main__":
    main()
