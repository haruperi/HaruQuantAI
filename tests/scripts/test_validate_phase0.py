"""Integration test for the complete Phase 0 evidence validator."""

from __future__ import annotations

from scripts import validate_phase0


def test_phase0_evidence_is_internally_consistent() -> None:
    """Checked-in Phase 0 evidence satisfies every deterministic readiness gate."""
    assert validate_phase0.validate() == []
