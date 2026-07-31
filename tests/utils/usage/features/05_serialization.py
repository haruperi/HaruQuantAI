"""Executable canonical-serialization examples."""

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    canonical_digest,
    canonical_json,
    to_json_safe,
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


def fr_utils_013_to_json_safe() -> None:
    """FR-UTL-013: Stage 1 — Convert supported values into deterministic JSON-safe primitives."""
    _header("Stage 1: Arbitrary Value Coercion - To JSON Safe (FR-UTL-013)")
    safe = to_json_safe({"amount": Decimal("1.2300")})
    print(_format_result(safe))
    print(f"Data -> json_safe_mapping={safe}")


def fr_utils_015_reject_unsafe_value() -> None:
    """FR-UTL-015: Stage 2 — Demonstrate fail-closed unsupported-value handling."""
    _header("Stage 2: Validation - Reject Unsafe Value (FR-UTL-015)")
    try:
        canonical_json({"unsafe": object()})
    except Exception as exc:  # noqa: BLE001 - public serializer hides internal error classes.
        print(_format_result(exc))
        print(f"Data -> Serialization validation: unsafe value rejected ({exc})")


def fr_utils_014_canonical_json() -> None:
    """FR-UTL-014: Stage 3 — Serialize a mapping with stable key ordering."""
    _header("Stage 3: Canonical Output - Canonical JSON Serialization (FR-UTL-014)")
    json_str = canonical_json({"b": 2, "a": 1})
    print(_format_result(json_str))
    print(f"Data -> canonical_json='{json_str}'")


def fr_utils_036_canonical_digest() -> None:
    """FR-UTL-036: Stage 3 — Digest a trusted structure larger than item ceiling."""
    _header("Stage 3: Canonical Output - Stable Canonical Digest (FR-UTL-036)")
    oversized = {"records": [{"i": index} for index in range(20_000)]}
    digest = canonical_digest(oversized)
    print(_format_result(digest))
    print(f"Data -> canonical_digest='{digest}', records_count=20000")


def main() -> None:
    """Run all serialization examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-UTIL-04 — serialization/ — Canonical JSON Serialization and Safe Conversion\n\n"
        "Purpose: Provide deterministic canonical JSON formatting and stable digest computation.\n\n"
        "Module flow:\n"
        "-> arbitrary domain value\n"
        "-> JSON-safe coercion\n"
        "-> canonical JSON or digest"
    )

    # Stage 1: Arbitrary domain value coercion
    fr_utils_013_to_json_safe()

    # Stage 2: JSON-safe coercion and fail-closed validation
    fr_utils_015_reject_unsafe_value()

    # Stage 3: Canonical JSON or digest outputs
    fr_utils_014_canonical_json()
    fr_utils_036_canonical_digest()


if __name__ == "__main__":
    main()
