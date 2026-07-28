"""WF-UTL-005: normalize, resolve, and route one canonical error end to end."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.utils import (
    get_common_error_catalog,
    get_error_metadata,
    map_exception,
    normalize_error_code,
    require_error_definition,
    route_error_event,
    validate_error_catalog,
)

WORKFLOW_ID = "WF-UTL-005"
STAGES = (
    "Load and structurally validate the shared error catalogue.",
    "Map a raw exception to its canonical domain error.",
    "Normalize the resulting code to canonical form.",
    "Require a definition for the normalized code, failing closed when absent.",
    "Resolve severity, retryability, and routing metadata.",
    "Route one redacted error event to the configured sink.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _report(label: str, payload: Mapping[str, str]) -> None:
    """Print the status and bounded data of one mapped error payload."""
    status = "fail" if payload.get("code") else "success"
    print(f"{label} status : {status}")
    print(f"{label} data   : {dict(payload)}")


def main() -> None:
    """Run the documented error normalization and routing workflow."""
    print(f"{WORKFLOW_ID} — Error Normalization, Metadata, and Routing")
    print("INPUT BOUNDARY — raw exception or domain error code")

    # Stage 1 — Load and structurally validate the shared error catalogue.
    _stage(1)
    catalog = get_common_error_catalog()
    validated = validate_error_catalog(catalog)
    print("Catalogue entries    :", len(validated))
    print("Sample codes         :", sorted(validated)[:5])
    assert len(validated) == len(catalog)

    # Stage 2 — Map a raw exception to its canonical domain error.
    _stage(2)
    mapped = map_exception(RuntimeError("password=must-not-escape"))
    _report("mapped ", mapped)
    assert mapped["code"] == "INTERNAL_ERROR"
    assert "must-not-escape" not in str(mapped)
    print("Source payload withheld from mapping: True")

    # Stage 3 — Normalize the resulting code to canonical form.
    _stage(3)
    normalized = normalize_error_code(" validation failed ")
    print("Raw code             : ' validation failed '")
    print("Normalized code      :", normalized)
    assert normalized == "VALIDATION_FAILED"

    # Stage 4 — Require a definition for the normalized code, failing closed when absent.
    _stage(4)
    definition = require_error_definition(normalized, catalog)
    print("Definition domain    :", definition.domain)
    print("Definition category  :", definition.category)
    print("Definition retryable :", definition.retryable)
    try:
        require_error_definition("NOT_A_REGISTERED_CODE", catalog)
    except Exception as exc:  # noqa: BLE001 - public boundary hides internal classes.
        print("Unregistered code rejected:", type(exc).__name__)
    else:
        raise AssertionError("unregistered code unexpectedly accepted")

    # Stage 5 — Resolve severity, retryability, and routing metadata.
    _stage(5)
    metadata = get_error_metadata(normalized)
    print("Metadata title       :", metadata.title)
    print("Metadata severity    :", metadata.severity)
    print("Metadata retryable   :", metadata.retryable)
    assert metadata.code == normalized

    # Stage 6 — Route one redacted error event to the configured sink.
    _stage(6)
    delivered: list[Mapping[str, str]] = []
    routed = route_error_event(
        RuntimeError("token=must-not-escape"),
        delivered.append,
    )
    _report("routed ", routed)
    assert len(delivered) == 1
    assert delivered[0] == routed
    assert "must-not-escape" not in str(delivered[0])
    print("Sink invocations     :", len(delivered))

    print(
        "\nOUTPUT BOUNDARY — canonical error code, resolved metadata, and one routed event"
    )


if __name__ == "__main__":
    main()
