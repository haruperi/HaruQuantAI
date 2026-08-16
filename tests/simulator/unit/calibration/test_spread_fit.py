"""M1 spread-fit evidence for FEAT-SIM-17."""

from app.services.simulator import dump_calibration_artifact, fit_spread_calibration

from tests.simulator.unit.calibration.test_partition import identity, partitions, policy


def test_spread_fit_is_labelled_m1_lower_bound() -> None:
    """FR-SIM-181-182: fit scheduled regimes with the exact lower-bound label."""
    artifact = fit_spread_calibration(
        partitions(), identity=identity(), policy=policy()
    )
    dumped = dump_calibration_artifact(artifact)
    assert dumped["component"] == "spread"
    assert dumped["regime"] == "scheduled_metadata_only"
    assert (
        dumped["parameters"]["interpretation"]
        == "provider_m1_end_of_minute_lower_bound"
    )  # type: ignore[index]
    assert "ordinary.p50" in dumped["parameters"]  # type: ignore[operator]
    assert "scheduled_event.p50" in dumped["parameters"]  # type: ignore[operator]
