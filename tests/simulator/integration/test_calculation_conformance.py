"""Offline calculation conformance artifact tests."""

import hashlib
import json

from app.services.simulator import (
    get_calculation_model_identity,
    load_calculation_conformance_artifact,
    run_offline_calculation_conformance,
    unwrap_simulation_response,
)


def artifact(actual: str = "100.00") -> dict[str, object]:
    """Return one checksummed offline artifact."""
    identity = unwrap_simulation_response(
        get_calculation_model_identity(), operation="test.model_identity"
    )["model_hash"]
    material = {
        "schema_id": "simulation.calculation_conformance.v1",
        "model_identity": identity,
        "cases": [{"case_id": "profit-1", "expected": "100.00", "actual": actual}],
    }
    payload = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return {**material, "checksum": hashlib.sha256(payload.encode()).hexdigest()}


def test_all_admitted_provider_fixtures_match_exactly() -> None:
    """Exact fixture equality produces a model/artifact-bound pass."""
    loaded = unwrap_simulation_response(
        load_calculation_conformance_artifact(artifact()),
        operation="test.load_artifact",
    )
    verdict = unwrap_simulation_response(
        run_offline_calculation_conformance(loaded), operation="test.run_conformance"
    )
    assert verdict["passed"] is True
    assert verdict["case_count"] == 1


def test_artifact_tamper_or_fixture_mismatch_fails() -> None:
    """Checksum tamper blocks loading and exact mismatch blocks admission."""
    tampered = artifact()
    tampered["checksum"] = "0" * 64
    assert load_calculation_conformance_artifact(tampered).data is None
    loaded = unwrap_simulation_response(
        load_calculation_conformance_artifact(artifact("99.99")),
        operation="test.load_mismatch",
    )
    verdict = unwrap_simulation_response(
        run_offline_calculation_conformance(loaded), operation="test.run_mismatch"
    )
    assert verdict["passed"] is False
