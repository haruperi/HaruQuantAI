"""Schema and integrity gates for generated L5 operational certificates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.services.simulator import get_parity_envelope

from tests.simulator.integration.l5_certificate_collection import (
    validate_l5_certificate_bundle,
    write_certificate_bundle,
)
from tests.simulator.integration.test_parity_relationships import paired_evidence


def _synthetic_schema_fixture(bundle: Path) -> None:
    """Create non-certifying fixture bytes for validator tests only."""
    envelope = get_parity_envelope("v2")
    applicability = envelope["operational_applicability"]
    scope = envelope["certificate_scope"]
    assert isinstance(applicability, dict)
    assert isinstance(scope, dict)
    left, right = paired_evidence()
    write_certificate_bundle(
        bundle,
        manifest={
            "schema_version": "l5-mt5-operational-certificate.v1",
            "certificate_id": "schema-fixture-not-a-certificate",
            "envelope_version": "v2",
            "evidence_route": applicability["evidence_route"],
            "provider_routes": applicability["provider_routes"],
            "certified_semantics": applicability["certified_semantics"],
            "excluded_empirical_claims": applicability["excluded_empirical_claims"],
            "asset_class": scope["asset_class"],
            "status": "valid",
            "test_fixture_only": True,
        },
        left=left,
        right=right,
        environment={
            "environment": "dev",
            "provider": "mt5",
            "route": "demo",
            "target_build": "schema-fixture",
            "server_digest": "a" * 64,
            "subject_digest": "b" * 64,
            "secret_free": True,
        },
        command="schema fixture; no provider operation",
    )


def test_l5_certificate_bundle_schema_and_checksums_reproduce(tmp_path: Path) -> None:
    """A complete, secret-free, reproducible fixture passes every gate."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    validate_l5_certificate_bundle(bundle)


def test_l5_certificate_bundle_rejects_tampered_evidence(tmp_path: Path) -> None:
    """Normalized evidence tampering fails before certificate acceptance."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    normalized = bundle / "normalized-right.json"
    payload = json.loads(normalized.read_text(encoding="utf-8"))
    payload["canonical_digest"] = "0" * 64
    normalized.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="normalized right evidence"):
        validate_l5_certificate_bundle(bundle)
