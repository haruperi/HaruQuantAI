"""Untouched certification holdout and validation-policy evidence."""

from datetime import timedelta

from app.services.simulator import (
    fit_spread_calibration,
    validate_calibration_artifact,
)

from tests.simulator.unit.calibration.test_partition import (
    NOW,
    identity,
    partitions,
    policy,
)


def test_fit_cannot_receive_holdout_and_validation_uses_predeclared_policy() -> None:
    """FR-SIM-185/226/227: fitting is isolated and drift invalidates validity."""
    bundle = partitions()
    artifact = fit_spread_calibration(bundle, identity=identity(), policy=policy())
    verdict = validate_calibration_artifact(artifact, bundle, evaluated_at=NOW)
    assert verdict["valid"] is True
    expired = validate_calibration_artifact(
        artifact, bundle, evaluated_at=NOW + timedelta(days=31)
    )
    assert expired == {
        "valid": False,
        "reason": "calibration_expired",
        "observed_error": None,
    }
