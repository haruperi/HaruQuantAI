"""Schema and integrity gates for generated L5 operational certificates."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tests.simulator.integration.l5_certificate_collection import (
    build_certificate_manifest,
    build_collection_command,
    validate_l5_certificate_bundle,
    write_certificate_bundle,
)
from tests.simulator.integration.l5_certificate_finalize import (
    build_required_audit_commands,
    finalize_certificate_command_evidence,
    validate_finalized_command_ledger,
)
from tests.simulator.integration.test_parity_relationships import paired_evidence


def _synthetic_schema_fixture(
    bundle: Path, *, command_output: Path | None = None
) -> None:
    """Create non-certifying fixture bytes for validator tests only."""
    left, right = paired_evidence()
    environment = {
        "environment": "dev",
        "provider": "mt5",
        "route": "demo",
        "provider_build": "schema-fixture",
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
        application_build={
            "version": "2.2.11",
            "source_file_count": 3,
            "source_config_digest": "c" * 64,
        },
        provider_build="schema-fixture",
        authority_watermark={
            "orders": {"count": 0, "latest": None},
            "deals": {"count": 0, "latest": None},
            "transactions": {"count": 0, "latest": None},
        },
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
        command=build_collection_command(
            certificate_id="schema-fixture-not-a-certificate",
            symbol="EURUSD",
            output=command_output
            or Path(
                "artifacts/sim_live_parity/mt5-operational/v2/"
                "schema-fixture-not-a-certificate"
            ),
        ),
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


def test_l5_certificate_bundle_rejects_provider_build_substitution(
    tmp_path: Path,
) -> None:
    """The observed provider build cannot replace the application build."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_build"] = "different-provider-build"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="application/provider build"):
        validate_l5_certificate_bundle(bundle)


def test_l5_certificate_bundle_rejects_application_build_tampering(
    tmp_path: Path,
) -> None:
    """Changed application source identity invalidates its trigger binding."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["application_build"]["source_config_digest"] = "0" * 64
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="invalidation bindings"):
        validate_l5_certificate_bundle(bundle)


def test_l5_certificate_bundle_rejects_timestamp_only_watermark(
    tmp_path: Path,
) -> None:
    """Wall-clock time alone is not reconciled order/deal/transaction authority."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["initial_authority"]["last_reconciled_authority_watermark"] = (
        "2026-08-16T00:00:00+00:00"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="watermark is incomplete"):
        validate_l5_certificate_bundle(bundle)


def test_l5_certificate_bundle_rejects_absolute_collection_command(
    tmp_path: Path,
) -> None:
    """Workstation-specific absolute output paths cannot enter evidence."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    commands = bundle / "commands.txt"
    commands.write_text(
        "uv run python tests/simulator/integration/l5_certificate_collection.py "
        "--execute-demo --symbol BTCUSD --certificate-id "
        "schema-fixture-not-a-certificate --output "
        "C:/private/workspace/schema-fixture-not-a-certificate\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="repository-relative"):
        validate_l5_certificate_bundle(bundle)


def _finalization_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Create one candidate under the required generated-artifact root."""
    root = tmp_path / "workspace"
    relative = Path(
        "artifacts/sim_live_parity/scope/v2/schema-fixture-not-a-certificate"
    )
    bundle = root / relative
    bundle.parent.mkdir(parents=True)
    _synthetic_schema_fixture(bundle, command_output=relative)
    return root, bundle


def test_certificate_finalization_records_exact_successful_audits(
    tmp_path: Path,
) -> None:
    """Successful mandatory commands become checksummed deterministic evidence."""
    root, bundle = _finalization_fixture(tmp_path)
    observed: list[tuple[str, ...]] = []

    def runner(arguments, workspace_root):
        assert workspace_root == root
        observed.append(tuple(arguments))
        return 0

    finalize_certificate_command_evidence(
        bundle,
        workspace_root=root,
        runner=runner,
    )
    assert tuple(observed) == build_required_audit_commands(bundle.relative_to(root))
    validate_l5_certificate_bundle(bundle)
    validate_finalized_command_ledger(bundle, root)
    assert all(
        line.startswith("exit_code=0\t")
        for line in (bundle / "commands.txt").read_text(encoding="utf-8").splitlines()
    )


def test_certificate_finalization_rejects_repeated_finalization(tmp_path: Path) -> None:
    """An immutable finalized ledger cannot be rewritten."""
    root, bundle = _finalization_fixture(tmp_path)
    finalize_certificate_command_evidence(
        bundle,
        workspace_root=root,
        runner=lambda _arguments, _root: 0,
    )
    with pytest.raises(ValueError, match="already finalized"):
        finalize_certificate_command_evidence(
            bundle,
            workspace_root=root,
            runner=lambda _arguments, _root: 0,
        )


def test_failed_audit_preserves_original_candidate_bytes(tmp_path: Path) -> None:
    """A failed command leaves the candidate ledger and checksums untouched."""
    root, bundle = _finalization_fixture(tmp_path)
    commands_before = (bundle / "commands.txt").read_bytes()
    checksums_before = (bundle / "checksums.sha256").read_bytes()

    def runner(arguments, workspace_root):
        del workspace_root
        return 7 if "pytest" in arguments else 0

    with pytest.raises(RuntimeError, match="exit code 7"):
        finalize_certificate_command_evidence(
            bundle,
            workspace_root=root,
            runner=runner,
        )
    assert (bundle / "commands.txt").read_bytes() == commands_before
    assert (bundle / "checksums.sha256").read_bytes() == checksums_before


def test_finalized_ledger_rejects_failed_or_changed_commands(tmp_path: Path) -> None:
    """Exit-code or command drift cannot pass final publication validation."""
    root, bundle = _finalization_fixture(tmp_path)
    finalize_certificate_command_evidence(
        bundle,
        workspace_root=root,
        runner=lambda _arguments, _root: 0,
    )
    commands = bundle / "commands.txt"
    original = commands.read_text(encoding="utf-8")
    commands.write_text(
        original.replace("exit_code=0", "exit_code=1", 1), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="failed command"):
        validate_finalized_command_ledger(bundle, root)
    commands.write_text(
        original.replace("ruff check .", "ruff check tests", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="differs"):
        validate_finalized_command_ledger(bundle, root)


def test_finalizer_inert_modes_execute_from_a_fresh_process(tmp_path: Path) -> None:
    """Direct validation and scanning bootstrap repository-local imports."""
    bundle = tmp_path / "bundle"
    _synthetic_schema_fixture(bundle)
    repository_root = Path(__file__).resolve().parents[3]
    script = "tests/simulator/integration/l5_certificate_finalize.py"
    uv_executable = shutil.which("uv")
    assert uv_executable is not None
    for mode in ("--validate-only", "--scan-only"):
        result = subprocess.run(  # noqa: S603 - exact repository test command.
            (
                uv_executable,
                "run",
                "python",
                script,
                mode,
                "--bundle",
                str(bundle),
            ),
            cwd=repository_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
