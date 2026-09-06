"""Determinism and catalogue-reconciliation tests for MQL5-based contracts."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST = REPO_ROOT / "docs" / "dev" / "MQL5_Contract_Value_Manifest.json"
CLASSIFICATION = (
    REPO_ROOT
    / "docs"
    / "dev"
    / "MQL5_Constants_Enumerations_Structures_Classification.md"
)


def test_generator_check_is_clean() -> None:
    """The checked-in focused modules are byte-identical to generator output."""
    subprocess.run(
        [sys.executable, "scripts/generate_mql5_contracts.py", "--check"],
        cwd=REPO_ROOT,
        check=True,
    )


def test_every_manifest_contract_is_exposed_once() -> None:
    """Every accepted non-structure row resolves from its routed owner module."""
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert document["counts"] == {
        "accepted_non_structure_rows": 1859,
        "accepted_rows": 1983,
        "classification_rows": 2408,
        "rejected_rows": 425,
    }
    for entry in document["contracts"]:
        module_name = entry["module"].removesuffix(".py").replace("/", ".")
        module = importlib.import_module(module_name)
        assert hasattr(module, entry["contract"]), entry["contract"]


def test_rejected_enum_positions_are_evidence_only() -> None:
    """Rejected cryptography members preserve gaps without becoming exports."""
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = document["enum_sources"]["ENUM_CRYPT_METHOD"]
    assert [(row["identifier"], row["position"]) for row in source] == [
        ("CRYPT_BASE64", 0),
        ("CRYPT_AES128", 1),
        ("CRYPT_AES256", 2),
        ("CRYPT_DES", 3),
        ("CRYPT_HASH_SHA1", 4),
        ("CRYPT_HASH_SHA256", 5),
        ("CRYPT_HASH_MD5", 6),
        ("CRYPT_ARCH_ZIP", 7),
    ]
    module = importlib.import_module("app.contracts.interfaces.io_constants")
    assert not hasattr(module, "CRYPT_DES")
    assert not hasattr(module, "CRYPT_HASH_SHA1")
    assert not hasattr(module, "CRYPT_HASH_MD5")


def test_all_rejected_identifiers_are_absent_from_generated_modules() -> None:
    """None of the 425 rejected source names leaks into generated exports."""
    rejected: set[str] = set()
    for line in CLASSIFICATION.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith(("| ---", "| Identifier")):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[4] == "Rejected adoption":
            rejected.add(cells[0])
    assert len(rejected) == 425

    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    generated_exports: set[str] = set()
    for module_path in {entry["module"] for entry in document["contracts"]}:
        module_name = module_path.removesuffix(".py").replace("/", ".")
        module = importlib.import_module(module_name)
        generated_exports.update(module.__all__)
    assert rejected.isdisjoint(generated_exports)
