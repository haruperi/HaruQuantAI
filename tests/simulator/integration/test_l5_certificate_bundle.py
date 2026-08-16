"""Schema and integrity gates for generated L5 operational certificates."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tests.simulator.integration.l5_certificate_collection import (
    build_certificate_manifest,
    validate_l5_certificate_bundle,
    write_certificate_bundle,
)
from tests.simulator.integration.test_parity_relationships import paired_evidence


def _synthetic_schema_fixture(bundle: Path) -> None:
    """Create non-certifying fixture bytes for validator tests only."""
    left, right = paired_evidence()
    environment = {
        "environment": "dev",
        "provider": "mt5",
        "route": "demo",
        "target_build": "schema-fixture",
        "server_digest": "a" * 64,
        "subject_digest": "b" * 64,
        "secret_free": True,
    }
    interval_end = datetime.fromisoformat(str(left["evaluation_time"]))
    manifest = build_certificate_manifest(
        certificate_id="schema-fixture-not-a-certificate",
        symbol="EURUSD",
        specification={"provider_symbol": "EURUSD", "revision": "fixture-v1"},
        interval_start=interval_end - timedelta(seconds=3),
        interval_end=interval_end,
        left=left,
        right=right,
        environment=environment,
        account_modes={
            "trade_mode": "demo",
            "margin_mode": "netting",
            "margin_so_mode": "percent",
        },
        issued_at=datetime(2026, 8, 14, tzinfo=UTC),
    )
    manifest["test_fixture_only"] = True
    write_certificate_bundle(
        bundle,
        manifest=manifest,
        left=left,
        right=right,
        environment=environment,
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


@pytest.mark.parametrize(
    "field",
    [
        "admitted_specifications",
        "initial_authority",
        "comparison_contract",
        "evidence_provenance",
        "invalidation_bindings",
    ],
)
def test_l5_certificate_bundle_rejects_missing_publication_field(
    tmp_path: Path, field: str
) -> None:
    """Every mandatory publication field fails closed when removed."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest[field]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="manifest fields"):
        validate_l5_certificate_bundle(bundle)


def test_l5_certificate_bundle_rejects_invalidation_binding_tampering(
    tmp_path: Path,
) -> None:
    """A changed build binding invalidates the publication manifest."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["invalidation_bindings"]["build_identity_change"] = "0" * 64
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="invalidation bindings"):
        validate_l5_certificate_bundle(bundle)
