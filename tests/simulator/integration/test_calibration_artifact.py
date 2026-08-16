"""Calibration artifact round-trip and scope integration evidence."""

import json
import socket
import subprocess
import sys

import pytest
from app.services.simulator import (
    dump_calibration_artifact,
    fit_spread_calibration,
    load_calibration_artifact,
)

from tests.simulator.unit.calibration.test_partition import identity, partitions, policy


def test_artifact_round_trip_preserves_demo_scope_and_checksum() -> None:
    """FR-SIM-186/224: checksummed demo artifacts cannot imply live scope."""
    artifact = fit_spread_calibration(
        partitions(), identity=identity(), policy=policy()
    )
    dumped = dump_calibration_artifact(artifact)
    loaded = load_calibration_artifact(dumped)
    assert dump_calibration_artifact(loaded) == dumped
    assert dumped["environment"] == "demo"
    assert dumped["applicability"]["environment"] == "demo"  # type: ignore[index]


def test_demo_evidence_cannot_be_relabelled_live() -> None:
    """FR-SIM-186: artifact identity cannot expand demo evidence to live."""
    with pytest.raises(ValueError, match="cannot relabel"):
        fit_spread_calibration(
            partitions(), identity=identity(environment="live"), policy=policy()
        )


def test_artifact_threshold_mutation_fails_checksum_verification() -> None:
    """FR-SIM-224/227: a post-fit threshold change invalidates the artifact."""
    artifact = fit_spread_calibration(
        partitions(), identity=identity(), policy=policy()
    )
    dumped = dump_calibration_artifact(artifact)
    dumped["threshold_tolerance"] = "999"
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_calibration_artifact(dumped)


def test_artifact_checksum_is_stable_across_processes() -> None:
    """FR-SIM-224: fresh processes verify the identical artifact checksum."""
    artifact = fit_spread_calibration(
        partitions(), identity=identity(), policy=policy()
    )
    dumped = dump_calibration_artifact(artifact)
    program = (
        "import json,sys;"
        "from app.services.simulator import load_calibration_artifact,dump_calibration_artifact;"
        "value=json.loads(sys.stdin.read());"
        "print(dump_calibration_artifact(load_calibration_artifact(value))['checksum'])"
    )
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and inline program.
        [sys.executable, "-c", program],
        input=json.dumps(dumped),
        capture_output=True,
        check=True,
        text=True,
        timeout=5,
    )
    assert completed.stdout.strip() == dumped["checksum"]


def test_calibration_fit_is_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-SIM-224: fitting performs no network interaction."""

    def blocked_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    fit_spread_calibration(partitions(), identity=identity(), policy=policy())
