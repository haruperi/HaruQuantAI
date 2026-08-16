"""Schema and integrity gates for generated L5 operational certificates."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from app.services.simulator import (
    compare_parity_evidence,
    get_parity_envelope,
    normalize_parity_evidence,
)

from tests.simulator.integration.test_parity_relationships import paired_evidence

_BUNDLE_FILES = frozenset(
    {
        "manifest.json",
        "left-evidence.json",
        "right-evidence.json",
        "normalized-left.json",
        "normalized-right.json",
        "comparison.json",
        "commands.txt",
        "environment.json",
        "checksums.sha256",
    }
)
_HASHED_FILES = _BUNDLE_FILES - {"checksums.sha256"}
_SENSITIVE_FRAGMENTS = (
    "account_id",
    "credential",
    "login",
    "password",
    "secret",
    "terminal_path",
    "token",
)


def _json(path: Path) -> dict[str, object]:
    """Read one JSON object from the bundle.

    Args:
        path: Exact bundle member path.

    Returns:
        Parsed JSON object.

    Raises:
        TypeError: If the member is not a JSON object.
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"bundle member is not a JSON object: {path.name}")
    return value


def _digest(path: Path) -> str:
    """Return one member's lowercase SHA-256 digest.

    Args:
        path: Exact bundle member path.

    Returns:
        Lowercase SHA-256 digest.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _has_sensitive_key(value: object) -> bool:
    """Return whether nested JSON carries a forbidden sensitive field name."""
    if isinstance(value, Mapping):
        for key, nested in value.items():
            lowered = str(key).lower()
            if lowered != "secret_free" and any(
                fragment in lowered for fragment in _SENSITIVE_FRAGMENTS
            ):
                return True
            if _has_sensitive_key(nested):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return any(_has_sensitive_key(item) for item in value)
    return False


def _validate_manifest(
    manifest: Mapping[str, object], envelope: Mapping[str, object]
) -> None:
    """Validate manifest identity, applicability, and exclusions."""
    applicability = envelope.get("operational_applicability")
    scope = envelope.get("certificate_scope")
    if not isinstance(applicability, Mapping):
        raise TypeError("Envelope v2 operational applicability is malformed")
    if not isinstance(scope, Mapping):
        raise TypeError("Envelope v2 certificate scope is malformed")
    expected = {
        "schema_version": "l5-mt5-operational-certificate.v1",
        "envelope_version": "v2",
        "evidence_route": applicability["evidence_route"],
        "provider_routes": applicability["provider_routes"],
        "certified_semantics": applicability["certified_semantics"],
        "excluded_empirical_claims": applicability["excluded_empirical_claims"],
        "asset_class": scope["asset_class"],
        "status": "valid",
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("certificate manifest differs from Envelope v2")


def _validate_evidence(bundle: Path, envelope: Mapping[str, object]) -> None:
    """Reproduce both normalized traces and their comparison."""
    left = _json(bundle / "left-evidence.json")
    right = _json(bundle / "right-evidence.json")
    if (
        left.get("certificate_target") != "demo"
        or right.get("certificate_target") != "demo"
    ):
        raise ValueError("both evidence sides must retain demo scope")
    actual_left = normalize_parity_evidence(left, envelope)
    actual_right = normalize_parity_evidence(right, envelope)
    if (
        _json(bundle / "normalized-left.json") != actual_left
        or _json(bundle / "normalized-right.json") != actual_right
    ):
        raise ValueError("normalized evidence does not reproduce")
    comparison = _json(bundle / "comparison.json")
    actual_comparison = compare_parity_evidence(left, right, envelope)
    if comparison != actual_comparison or comparison.get("passed") is not True:
        raise ValueError("certificate comparison does not reproduce or pass")


def _validate_environment(bundle: Path) -> None:
    """Validate bounded collection identity and credential hygiene."""
    environment = _json(bundle / "environment.json")
    expected = {"environment": "dev", "provider": "mt5", "route": "demo"}
    if any(environment.get(key) != value for key, value in expected.items()):
        raise ValueError("certificate environment must identify dev/MT5/demo")
    if environment.get("secret_free") is not True:
        raise ValueError("certificate environment lacks a secret-free attestation")
    for name in _HASHED_FILES:
        if name.endswith(".json") and _has_sensitive_key(_json(bundle / name)):
            raise ValueError("certificate bundle contains a sensitive field name")
    commands = (bundle / "commands.txt").read_text(encoding="utf-8").lower()
    if any(fragment in commands for fragment in _SENSITIVE_FRAGMENTS):
        raise ValueError("certificate commands contain sensitive material")


def _validate_checksums(bundle: Path) -> None:
    """Validate the complete deterministic member checksum inventory."""
    checksum_lines = (
        (bundle / "checksums.sha256").read_text(encoding="utf-8").splitlines()
    )
    expected_lines = [
        f"{_digest(bundle / name)}  {name}" for name in sorted(_HASHED_FILES)
    ]
    if checksum_lines != expected_lines:
        raise ValueError("certificate bundle checksums do not reproduce")


def validate_l5_certificate_bundle(bundle: Path) -> None:
    """Validate one generated L5-MT5-Operational certificate bundle.

    Args:
        bundle: Resolved directory containing exactly one certificate bundle.

    Raises:
        ValueError: If schema, scope, exclusions, comparison, secrecy, or an
            integrity checksum is invalid.
    """
    if not bundle.is_dir():
        raise ValueError("certificate bundle directory is absent")
    members = {path.name for path in bundle.iterdir() if path.is_file()}
    if members != _BUNDLE_FILES:
        raise ValueError("certificate bundle members are incomplete or unexpected")
    envelope = get_parity_envelope("v2")
    _validate_manifest(_json(bundle / "manifest.json"), envelope)
    _validate_evidence(bundle, envelope)
    _validate_environment(bundle)
    _validate_checksums(bundle)


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    """Write deterministic test-only JSON.

    Args:
        path: Destination beneath pytest's temporary directory.
        value: JSON-safe mapping.
    """
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _synthetic_schema_fixture(bundle: Path) -> None:
    """Create non-certifying fixture bytes for validator tests only.

    Args:
        bundle: Pytest-owned temporary destination.
    """
    bundle.mkdir()
    envelope = get_parity_envelope("v2")
    applicability = envelope["operational_applicability"]
    left, right = paired_evidence()
    _write_json(bundle / "left-evidence.json", left)
    _write_json(bundle / "right-evidence.json", right)
    _write_json(
        bundle / "normalized-left.json",
        normalize_parity_evidence(left, envelope),
    )
    _write_json(
        bundle / "normalized-right.json",
        normalize_parity_evidence(right, envelope),
    )
    _write_json(
        bundle / "comparison.json",
        compare_parity_evidence(left, right, envelope),
    )
    _write_json(
        bundle / "manifest.json",
        {
            "schema_version": "l5-mt5-operational-certificate.v1",
            "certificate_id": "schema-fixture-not-a-certificate",
            "envelope_version": "v2",
            "evidence_route": applicability["evidence_route"],
            "provider_routes": applicability["provider_routes"],
            "certified_semantics": applicability["certified_semantics"],
            "excluded_empirical_claims": applicability["excluded_empirical_claims"],
            "asset_class": envelope["certificate_scope"]["asset_class"],
            "status": "valid",
            "test_fixture_only": True,
        },
    )
    _write_json(
        bundle / "environment.json",
        {
            "environment": "dev",
            "provider": "mt5",
            "route": "demo",
            "target_build": "schema-fixture",
            "server_digest": "a" * 64,
            "subject_digest": "b" * 64,
            "secret_free": True,
        },
    )
    (bundle / "commands.txt").write_text(
        "schema fixture; no provider operation\n", encoding="utf-8"
    )
    (bundle / "checksums.sha256").write_text(
        "\n".join(f"{_digest(bundle / name)}  {name}" for name in sorted(_HASHED_FILES))
        + "\n",
        encoding="utf-8",
    )


def test_l5_certificate_bundle_schema_and_checksums_reproduce(tmp_path: Path) -> None:
    """A complete v2 bundle reproduces every normalized result and checksum."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    validate_l5_certificate_bundle(bundle)


def test_l5_certificate_bundle_rejects_tampered_evidence(tmp_path: Path) -> None:
    """Any post-publication evidence mutation invalidates bundle integrity."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    left = _json(bundle / "left-evidence.json")
    left["evaluation_time"] = "2026-08-20T12:00:01+00:00"
    _write_json(bundle / "left-evidence.json", left)
    with pytest.raises(ValueError, match="normalized evidence does not reproduce"):
        validate_l5_certificate_bundle(bundle)
