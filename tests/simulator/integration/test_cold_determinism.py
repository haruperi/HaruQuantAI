"""Integration tests for cold re-execution determinism of parity evidence."""

from app.services.simulator import (
    compare_parity_evidence,
    get_parity_envelope,
    normalize_parity_evidence,
)

from tests.simulator.integration.test_parity_relationships import (
    paired_evidence,
)

_ENVELOPE = get_parity_envelope("v1")


def test_cold_runs_from_fresh_roots_are_identical() -> None:
    """Standing regression: cold re-execution from fresh roots is identical."""
    first_left, first_right = paired_evidence()
    second_left, second_right = paired_evidence()
    # Fresh roots: the second construction independently allocates different
    # raw identifiers, trace values, and provider observation timestamps.
    second_right["orders"][0]["provider_timestamp"] = (  # type: ignore[index]
        "2026-08-20T11:00:42+00:00"
    )
    views = [
        normalize_parity_evidence(side, _ENVELOPE)
        for side in (first_left, first_right, second_left, second_right)
    ]
    digests = {view["canonical_digest"] for view in views}
    assert len(digests) == 1
    first = compare_parity_evidence(first_left, first_right, _ENVELOPE)
    second = compare_parity_evidence(second_left, second_right, _ENVELOPE)
    assert first["passed"] is True
    assert second["passed"] is True
    assert first["failures"] == second["failures"] == []


def test_normalization_digest_is_stable_across_processes() -> None:
    """FR-SIM-189: the canonical digest is a stable pure function of evidence."""
    left, _right = paired_evidence()
    first = normalize_parity_evidence(left, _ENVELOPE)
    second = normalize_parity_evidence(left, _ENVELOPE)
    assert first["canonical_digest"] == second["canonical_digest"]
