"""Execution-trace calibration evidence for FEAT-SIM-17."""

from app.services.simulator import (
    dump_calibration_artifact,
    fit_execution_calibration,
    get_calibration_applicability,
)

from tests.simulator.unit.calibration.test_partition import identity, partitions, policy


def test_execution_fit_excludes_unsupported_components() -> None:
    """FR-SIM-183-184: insufficient components remain explicit exclusions."""
    artifact = fit_execution_calibration(
        partitions(),
        components=("latency", "slippage", "partial_fill"),
        identity=identity(),
        policy=policy(),
    )
    dumped = dump_calibration_artifact(artifact)
    applicability = get_calibration_applicability(artifact)
    assert "latency.mean" in dumped["parameters"]  # type: ignore[operator]
    assert applicability["exclusions"] == (
        "partial_fill:insufficient_evidence",
        "slippage:insufficient_evidence",
    )
