"""WF-UTL-006: derive trace identity and enforce UTC time discipline."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.utils import (
    age_seconds,
    derive_stable_id,
    format_utc_timestamp,
    generate_id,
    is_fresh,
    parse_utc_timestamp,
    utc_now,
    validate_id,
)

WORKFLOW_ID = "WF-UTL-006"
STAGES = (
    "Generate a new correlation identifier for an inbound operation.",
    "Derive a deterministic identifier from stable identity material.",
    "Validate a caller-supplied identifier before use.",
    "Read the current aware UTC instant from the shared clock.",
    "Parse and render inbound and outbound timestamps canonically.",
    "Evaluate evidence freshness against an explicit bound.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _report(label: str, status: str, data: object) -> None:
    """Print the status and bounded data of one workflow step."""
    print(f"{label} status : {status}")
    print(f"{label} data   : {data}")


def main() -> None:  # noqa: PLR0915
    """Run the documented identity and UTC-time workflow."""
    print(f"{WORKFLOW_ID} — Trace Identity and UTC Time Discipline")
    print("INPUT BOUNDARY — caller-supplied identity seed or timestamp")

    # Stage 1 — Generate a new correlation identifier for an inbound operation.
    _stage(1)
    request_id = generate_id("req")
    correlation_id = generate_id("cor")
    _report("request", "success", request_id)
    _report("correl ", "success", correlation_id)
    assert request_id.startswith("req-")
    assert request_id != generate_id("req")

    # Stage 2 — Derive a deterministic identifier from stable identity material.
    _stage(2)
    material = "EURUSD|M15|2026-07-28T00:00:00Z"
    stable_id = derive_stable_id("id", material)
    repeated_id = derive_stable_id("id", material)
    _report("stable ", "success", stable_id)
    assert stable_id == repeated_id
    print("Deterministic across calls:", stable_id == repeated_id)

    # Stage 3 — Validate a caller-supplied identifier before use.
    _stage(3)
    validated = validate_id(request_id, expected_prefix="req")
    _report("valid  ", "success", validated)
    try:
        validate_id("not-a-canonical-identifier")
    except Exception as exc:  # noqa: BLE001 - public boundary hides internal classes.
        _report("invalid", "fail", type(exc).__name__)
    else:
        raise AssertionError("malformed identifier unexpectedly accepted")

    # Stage 4 — Read the current aware UTC instant from the shared clock.
    _stage(4)
    now = utc_now()
    _report("clock  ", "success", now.isoformat())
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)
    print("Aware UTC instant     :", True)

    # Stage 5 — Parse and render inbound and outbound timestamps canonically.
    _stage(5)
    rendered = format_utc_timestamp(now)
    parsed = parse_utc_timestamp(rendered)
    _report("render ", "success", rendered)
    _report("parse  ", "success", parsed.isoformat())
    assert parsed == now
    try:
        parse_utc_timestamp("2026-07-28T00:00:00")
    except Exception as exc:  # noqa: BLE001 - public boundary hides internal classes.
        _report("naive  ", "fail", type(exc).__name__)
    else:
        raise AssertionError("naive timestamp unexpectedly accepted")

    # Stage 6 — Evaluate evidence freshness against an explicit bound.
    _stage(6)
    reference = datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC)
    observed = reference - timedelta(seconds=30)
    age = age_seconds(observed, reference=reference)
    fresh = is_fresh(observed, reference=reference, max_age_seconds=Decimal(60))
    stale = is_fresh(observed, reference=reference, max_age_seconds=Decimal(10))
    _report("age    ", "success", f"{age} seconds")
    _report("fresh  ", "success" if fresh else "fail", fresh)
    _report("stale  ", "success" if not stale else "fail", stale)
    assert age == Decimal(30)
    assert fresh is True
    assert stale is False

    print(
        "\nOUTPUT BOUNDARY — validated trace identifier plus aware UTC instant and freshness verdict"
    )


if __name__ == "__main__":
    main()
