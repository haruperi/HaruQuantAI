"""Executable trace and stable-identity examples."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import derive_stable_id, generate_id, validate_id


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


def fr_utils_007_generate_id() -> None:
    """FR-UTL-007: Stage 1 — Generate a canonical UUID4 request identifier."""
    _header(
        "Stage 1: Identity Material - Generate Prefixed UUID4 Identifier (FR-UTL-007)"
    )
    req_id = generate_id("req")
    print(_format_result(req_id))
    print(f"Data -> generated_request_id='{req_id}'")


def fr_utils_009_derive_stable_id() -> None:
    """FR-UTL-009: Stage 1 — Derive a deterministic non-trace artifact identity."""
    _header(
        "Stage 1: Identity Material - Derive Deterministic Stable Identifier (FR-UTL-009)"
    )
    stable_id = derive_stable_id("id", "strategy:v1")
    print(_format_result(stable_id))
    print(f"Data -> stable_artifact_id='{stable_id}'")


def fr_utils_008_validate_id() -> None:
    """FR-UTL-008: Stage 2 & 3 — Validate a canonical UUID4 workflow identifier."""
    _header("Stage 2 & 3: Generation & Validation -> Canonical Identifier (FR-UTL-008)")
    value = generate_id("wf")
    validated = validate_id(value, expected_prefix="wf")
    print(_format_result(validated))
    print(f"Data -> validated_workflow_id='{validated}'")


def main() -> None:
    """Run all identity examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-UTIL-02 — identity/ — Trace Identifiers\n\n"
        "Purpose: Generate, validate, and deterministically derive secret-free trace identifiers used across every domain.\n\n"
        "Module flow:\n"
        "-> prefix/identity material\n"
        "-> generation or validation\n"
        "-> canonical secret-free identifier"
    )

    # Stage 1: Prefix / identity material generation & stable derivation
    fr_utils_007_generate_id()
    fr_utils_009_derive_stable_id()

    # Stage 2 & 3: Generation / validation -> Canonical output
    fr_utils_008_validate_id()


if __name__ == "__main__":
    main()
