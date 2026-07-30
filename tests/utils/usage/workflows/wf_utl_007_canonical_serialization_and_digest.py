"""WF-UTL-007: produce canonical serialization and a stable digest."""

from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.utils import (
    canonical_digest,
    canonical_json,
    get_default_redaction_policy,
    is_sensitive_key,
    redact_mapping_value,
    to_json_safe,
)

WORKFLOW_ID = "WF-UTL-007"
STAGES = (
    "Coerce arbitrary domain values to JSON-safe primitives.",
    "Redact sensitive keys before any bytes are produced.",
    "Serialize with deterministic key order and separators.",
    "Compute a stable digest over the canonical bytes.",
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


def main() -> None:
    """Run the documented canonical serialization and digest workflow."""
    print(f"{WORKFLOW_ID} — Canonical Serialization and Digest")
    print("INPUT BOUNDARY — arbitrary domain payload")

    payload = {
        "symbol": "EURUSD",
        "observed_at": datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC),
        "close": Decimal("1.08422"),
        "api_key": "must-not-escape",  # pragma: allowlist secret
        "records": 512,
    }

    # Stage 1 — Coerce arbitrary domain values to JSON-safe primitives.
    _stage(1)
    json_safe = to_json_safe(payload)
    _report("coerce ", "success", json_safe)
    assert isinstance(json_safe, dict)
    assert isinstance(json_safe["close"], str | float | int)

    # Stage 2 — Redact sensitive keys before any bytes are produced.
    _stage(2)
    policy = get_default_redaction_policy()
    print("Policy is default     :", policy is not None)
    print("api_key is sensitive  :", is_sensitive_key("api_key"))
    print("symbol is sensitive   :", is_sensitive_key("symbol"))
    redaction = redact_mapping_value(json_safe, policy)
    _report("redact ", "success", redaction.value)
    print("Redacted paths        :", list(redaction.redacted_paths))
    assert is_sensitive_key("api_key") is True
    assert "must-not-escape" not in str(redaction.value)

    # Stage 3 — Serialize with deterministic key order and separators.
    _stage(3)
    serialized = canonical_json(redaction.value)
    repeated = canonical_json(redaction.value)
    _report("json   ", "success", serialized)
    assert serialized == repeated
    keys_in_order = [
        part.split('"')[1] for part in serialized.split(",") if part.count('"') >= 2
    ]
    print("Deterministic repeat  :", serialized == repeated)
    print("First serialized keys :", keys_in_order[:3])

    # Stage 4 — Compute a stable digest over the canonical bytes.
    _stage(4)
    digest = canonical_digest(redaction.value)
    expected = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    _report("digest ", "success", digest)
    assert digest == expected
    assert digest == canonical_digest(redaction.value)
    print("Digest matches sha256 of canonical JSON:", digest == expected)

    print("\nOUTPUT BOUNDARY — deterministic redacted canonical JSON and stable digest")


if __name__ == "__main__":
    main()
