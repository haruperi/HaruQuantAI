"""Stage-labelled usage program for WF-UTL-008."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.utils import (
    build_event_envelope,
    build_exact_unit,
    build_profile_ref,
    is_duplicate_event,
    parse_event_envelope,
)

WORKFLOW_ID = "WF-UTL-008"
STAGES = (
    "Resolve a versioned profile reference.",
    "Construct an exact unit-bearing amount.",
    "Build a redacted and integrity-hashed event envelope.",
    "Parse and deduplicate the consumer mapping.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute the Utils-owned operational contract-envelope stages."""
    print(f"{WORKFLOW_ID} — Operational Contract Envelope")
    print("INPUT BOUNDARY — domain facts and explicit version evidence")
    # Stage 1 — Resolve a versioned profile reference.
    _stage(1)
    profile = build_profile_ref(
        profile_kind="risk", profile_id="prf-demo", version="1", content_hash="a" * 64
    )
    # Stage 2 — Construct an exact unit-bearing amount.
    _stage(2)
    amount = build_exact_unit("25", kind="MONEY", currency="USD")
    # Stage 3 — Build a redacted and integrity-hashed event envelope.
    _stage(3)
    envelope = build_event_envelope(
        event_id="evt-demo",
        source_id="sim",
        source_sequence=1,
        correlation_id="cor-demo",
        causation_id=None,
        deduplication_key="intent-demo",
        emitted_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"profile": profile, "amount": amount},
    )
    # Stage 4 — Parse and deduplicate the consumer mapping.
    _stage(4)
    parsed = parse_event_envelope(envelope)
    duplicate = is_duplicate_event(parsed, {"intent-demo"})
    print("SUCCESS: WF-UTL-008 operational contract envelope completed")
    print(f"Data -> schema_id={parsed['schema_id']!r}, duplicate={duplicate}")
    print("OUTPUT BOUNDARY — validated mapping and duplicate verdict")


if __name__ == "__main__":
    main()
