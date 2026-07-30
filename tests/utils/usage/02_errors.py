"""Executable shared-error examples."""

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    get_common_error_catalog,
    get_error_metadata,
    map_exception,
    normalize_error_code,
    require_error_definition,
    route_error_event,
    validate_error_catalog,
)


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


def fr_utils_005_exception_payload_mapping() -> None:
    """FR-UTL-005: Stage 1 — Map caught exception without exposing source text."""
    _header(
        "Stage 1: Exception Payload Mapping - Caught Exception -> Sanitized Dictionary (FR-UTL-005)"
    )
    payload = map_exception(ValueError("unsafe source detail"))
    print(_format_result(payload))
    print(f"Data -> code='{payload['code']}', detail='{payload['detail']}'")


def fr_utils_006_exception_extension() -> None:
    """FR-UTL-006: Stage 1 — Demonstrate a domain-owned shared-base extension."""
    _header(
        "Stage 1: Exception Extension - Caught Domain Exception -> Shared Base Code (FR-UTL-006)"
    )
    payload = map_exception(ValueError("DOMAIN_FAILURE"))
    print(_format_result(payload))
    print(f"Data -> extended_error_code='{payload['code']}'")


def fr_utils_004_typed_error_codes() -> None:
    """FR-UTL-004: Stage 2 — Display boundary-safe symbolic exception metadata."""
    _header("Stage 2: Deterministic Base Type - Typed Error Codes (FR-UTL-004)")
    meta = get_error_metadata("VALIDATION_FAILED")
    print(_format_result(meta))
    print(
        f"Data -> code='{meta.code}', severity='{meta.severity}', title='{meta.title}'"
    )


def fr_utils_034_error_metadata() -> None:
    """FR-UTL-034: Stage 2 — Normalize and retrieve immutable safe metadata."""
    _header("Stage 2: Metadata Lookup - Code Normalization and Definition (FR-UTL-034)")
    code = normalize_error_code("validation-failed")
    meta = get_error_metadata(code)
    print(_format_result(meta))
    print(f"Data -> normalized_code='{code}', title='{meta.title}'")


def fr_utils_048_error_catalogues() -> None:
    """FR-UTL-048: Stage 2 — Validate immutable business-neutral error definitions."""
    _header("Stage 2: Catalog Validation - Immutable Error Catalogue (FR-UTL-048)")
    catalog = get_common_error_catalog()
    validated = validate_error_catalog(catalog)
    defn = require_error_definition("VALIDATION_FAILED", validated)
    print(_format_result(defn))
    print(f"Data -> common_error_count={len(catalog)}, validated_code='{defn.code}'")


def fr_utils_035_route_error_event() -> None:
    """FR-UTL-035: Stage 3 — Route one safe payload through an injected sink."""
    _header("Stage 3: Boundary Evidence - Injected Sink Routing (FR-UTL-035)")
    events: list[Mapping[str, str]] = []
    routed = route_error_event(ValueError("VALIDATION_FAILED"), events.append)
    print(_format_result(routed))
    print(f"Data -> routed_code='{events[0]['code']}', sink_event_count={len(events)}")


def main() -> None:
    """Run all shared-error examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-UTIL-01 — errors/ — Shared Errors, Metadata, and Routing\n\n"
        "Purpose: Provide the minimal shared exception hierarchy, normalized metadata,\n"
        "secret-safe boundary mapping, and explicit injected event routing every domain can use.\n\n"
        "Module flow:\n"
        "-> caught exception\n"
        "-> deterministic shared base type\n"
        "-> sanitized boundary evidence"
    )

    # Stage 1: Caught exception mapping and domain extensions
    fr_utils_005_exception_payload_mapping()
    fr_utils_006_exception_extension()

    # Stage 2: Deterministic base type, metadata, and catalogue validation
    fr_utils_004_typed_error_codes()
    fr_utils_034_error_metadata()
    fr_utils_048_error_catalogues()

    # Stage 3: Sanitized boundary evidence and event routing
    fr_utils_035_route_error_event()


if __name__ == "__main__":
    main()
