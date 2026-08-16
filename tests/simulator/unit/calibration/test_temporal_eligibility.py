"""Temporal and source eligibility evidence for FEAT-SIM-17."""

import pytest
from app.services.simulator import (
    fit_spread_calibration,
    get_calibration_applicability,
    partition_calibration_evidence,
)

from tests.simulator.unit.calibration.test_partition import (
    NOW,
    SOURCE,
    evidence,
    identity,
    policy,
)


def test_late_availability_and_source_mismatch_fail_closed() -> None:
    """FR-SIM-225: prospective fits reject late or mismatched evidence."""
    with pytest.raises(ValueError, match="late availability"):
        partition_calibration_evidence(
            evidence(late=True), evaluation_start=NOW, source_identity=SOURCE
        )
    with pytest.raises(ValueError, match="source identity mismatch"):
        partition_calibration_evidence(
            evidence(), evaluation_start=NOW, source_identity="f" * 64
        )


def test_retrospective_fit_is_explicitly_exploratory_only() -> None:
    """FR-SIM-225: late evidence is admitted only under retrospective labelling."""
    partitions = partition_calibration_evidence(
        evidence(late=True),
        evaluation_start=NOW,
        source_identity=SOURCE,
        retrospective=True,
    )
    retrospective_policy = policy()
    retrospective_policy["retrospective"] = True
    artifact = fit_spread_calibration(
        partitions, identity=identity(), policy=retrospective_policy
    )
    applicability = get_calibration_applicability(artifact)
    assert applicability["retrospective"] is True
    assert "retrospective:exploratory_only" in applicability["exclusions"]
