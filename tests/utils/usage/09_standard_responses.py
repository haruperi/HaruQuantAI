"""Executable standard-response examples."""

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from typing import Any

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
    """FR-UTL-042..047: Build success and error response branches."""
    result = ExampleResult(value=42)
    success = success_response(
        result,
        message="Example completed",
        metadata=_metadata(),
    )
    assert success.data is result
    assert success.metadata.extensions["legacy_status"] == "completed"
    print("Raw standard response data:", success.data)

    failure = error_response(
        code="VALIDATION_FAILED",
        details={"field": "value"},
        message="Example validation failed",
        metadata=_metadata(),
        catalog=get_common_error_catalog(),
    )
    assert failure.data is None
    assert failure.error is not None
    print("Approved standard error:", failure.error.code)

    unexpected = exception_response(
        RuntimeError("secret=must-not-escape"),
        message="Example failed safely",
        metadata=_metadata(),
        catalog=get_common_error_catalog(),
    )
    assert unexpected.error is not None
    assert unexpected.error.code == "INTERNAL_ERROR"
    assert "must-not-escape" not in str(unexpected.model_dump(mode="json"))

    elapsed_ms = get_execution_ms(1_000_000, clock=lambda: 2_234_567)
    assert elapsed_ms == 1.235


def fr_utils_050_immutable_mapping_data() -> None:
    """FR-UTL-050: Preserve immutable mapping data through JSON serialization."""
    immutable_data = MappingProxyType({"example": ExampleResult(value=42)})
    immutable_success = success_response(
        immutable_data,
        message="Immutable example completed",
        metadata=_metadata(),
    )
    assert immutable_success.data is immutable_data
    assert immutable_success.model_dump(mode="json")["data"] == {
        "example": {"value": 42}
    }
    print("Immutable mapping response data:", immutable_success.data)


def main() -> None:
    """Run the standard-response example."""
    fr_utils_042_through_047_standard_response()
    fr_utils_050_immutable_mapping_data()


if __name__ == "__main__":
    main()
    print("Canonical response runtime type:", get_standard_response_type().__name__)
