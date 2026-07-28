"""WF-UTL-004: build the standard operation response envelope end to end."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from typing import Any

from app.utils import (
    build_response_metadata,
    error_response,
    exception_response,
    generate_id,
    get_common_error_catalog,
    get_execution_ms,
    success_response,
    utc_now,
)

WORKFLOW_ID = "WF-UTL-004"
STAGES = (
    "Record the aware UTC start instant for the operation.",
    "Assemble trace, version, and timing metadata for the envelope.",
    "Return a completed operation payload in a success envelope.",
    "Return a known domain failure as a canonical code with redacted detail.",
    "Convert an unexpected exception without leaking the source payload.",
    "Measure elapsed duration and attach it to the envelope metadata.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _report(label: str, response: Any) -> None:
    """Print the status and bounded data of one standard response."""
    status = "success" if response.error is None else "fail"
    print(f"{label} status : {status}")
    if response.error is None:
        print(f"{label} data   : {response.data}")
    else:
        print(f"{label} code   : {response.error.code}")
        print(f"{label} detail : {response.error.details}")
    print(f"{label} name   : {response.metadata.name}")


def _metadata(start_time: int) -> Any:
    """Build bounded response metadata for the demonstrated operation."""
    return build_response_metadata(
        name="utils.response_envelope_example",
        domain="utils",
        risk_level="none",
        request_id=generate_id("req"),
        start_time=start_time,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
        correlation_id=generate_id("cor"),
        extensions={"legacy_status": "completed", "legacy_warning_count": 0},
    )


def main() -> None:
    """Run the documented response-envelope workflow from outcome to envelope."""
    print(f"{WORKFLOW_ID} — Standard Operation Response Envelope")
    print("INPUT BOUNDARY — domain operation outcome and trace context")

    # Stage 1 — Record the aware UTC start instant for the operation.
    _stage(1)
    started_at = utc_now()
    start_time = time.perf_counter_ns()
    print("Operation started at :", started_at.isoformat())
    assert started_at.tzinfo is not None

    # Stage 2 — Assemble trace, version, and timing metadata for the envelope.
    _stage(2)
    metadata = _metadata(start_time)
    print("Metadata domain      :", metadata.domain)
    print("Metadata request id  :", metadata.request_id)
    print("Metadata read only   :", metadata.read_only)
    assert metadata.request_id.startswith("req-")

    # Stage 3 — Return a completed operation payload in a success envelope.
    _stage(3)
    payload = {"symbol": "EURUSD", "records_examined": 512}
    completed = success_response(
        payload,
        message="Example operation completed",
        metadata=_metadata(start_time),
    )
    _report("success", completed)
    assert completed.error is None
    assert completed.data is payload

    # Stage 4 — Return a known domain failure as a canonical code with redacted detail.
    _stage(4)
    catalog = get_common_error_catalog()
    print("Catalogue size       :", len(catalog))
    failed = error_response(
        code="VALIDATION_FAILED",
        details={"field": "symbol"},
        message="Example validation failed",
        metadata=_metadata(start_time),
        catalog=catalog,
    )
    _report("error  ", failed)
    assert failed.data is None
    assert failed.error is not None
    assert failed.error.code == "VALIDATION_FAILED"

    # Stage 5 — Convert an unexpected exception without leaking the source payload.
    _stage(5)
    unexpected = exception_response(
        RuntimeError("api_key=must-not-escape"),
        message="Example failed safely",
        metadata=_metadata(start_time),
        catalog=catalog,
    )
    _report("except ", unexpected)
    assert unexpected.error is not None
    assert unexpected.error.code == "INTERNAL_ERROR"
    assert "must-not-escape" not in str(unexpected.model_dump(mode="json"))
    print("Source payload withheld from envelope: True")

    # Stage 6 — Measure elapsed duration and attach it to the envelope metadata.
    _stage(6)
    deterministic_ms = get_execution_ms(1_000_000, clock=lambda: 2_234_567)
    print("Deterministic elapsed ms :", deterministic_ms)
    assert deterministic_ms == 1.235
    print("Envelope execution ms    :", completed.metadata.execution_ms)

    print(
        "\nOUTPUT BOUNDARY — uniform StandardResponse success, error, or exception envelope"
    )


if __name__ == "__main__":
    main()
