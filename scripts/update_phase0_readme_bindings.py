"""Normalize the 18 authoritative domain README Phase 0 bindings."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVICE_READMES = sorted((REPO / "app/services").glob("*/README.md"))
README_PATHS = [*SERVICE_READMES, REPO / "app/ui/README.md"]

PENDING_CONFIG_ROW = (
    "| PHASE0_BOUND | Existing registered `FeatureSpec.config_keys`, or no feature "
    "configuration for a planned owner unless this card explicitly declares a key. "
    "| Exact selected types/defaults only; request and profile fields are not implicit "
    "feature configuration. | As declared by the owner card. | Unknown keys and "
    "invalid "
    "values fail closed; implementation records manifest/config/README parity before "
    "COMPLETE. |"
)


def _git_blob(path: Path) -> str:
    """Return the working-tree Git blob ID for a source document."""
    result = subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _baseline_content(path: Path) -> str:
    """Read the approved clean-main README baseline from Git.

    Returns:
        UTF-8-decoded README content from ``HEAD``.
    """
    relative = path.relative_to(REPO).as_posix()
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=REPO,
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8")


def normalized(content: str, register_blob: str, plan_blob: str) -> str:
    """Return one README with documentary bindings and live source links normalized."""
    result = content.replace(
        "SQX/HaruQuantAI_Unified_Specification.md",
        "evidence/specification-drift.md",
    )
    result = result.replace(
        "HaruQuantAI_Feature_Requirement_Traceability_Register.md",
        "Feature_Requirement_Traceability_Register.md",
    )
    result = result.replace(
        "HaruQuantAI_Phased_Feature_Implementation_Plan.md",
        "Phased_Feature_Implementation_Plan.md",
    )
    result = result.replace(
        "Source fingerprints and unresolved bindings",
        "Source fingerprints and Phase 0 bindings",
    )
    old_operation_binding = (
        "Public operation/DTO symbols in the selected contract; literal binding "
        "remains open."
    )
    new_operation_binding = (
        "Selected public operation/DTO surface; exact existing symbols are "
        "inventoried in the Phase 0 contract-binding projection."
    )
    result = result.replace(old_operation_binding, new_operation_binding)
    old_contract_binding = (
        "bind to the compatible selected contract before implementation; no "
        "alternate signature is invented here."
    )
    new_contract_binding = (
        "the selected target, operation scope, request/result union and typed "
        "failure semantics in this card are frozen; exact existing symbols are "
        "inventoried in `docs/dev/evidence/contract-bindings.json`, and a planned "
        "contract retains this binding without claiming runtime certification."
    )
    result = result.replace(old_contract_binding, new_contract_binding)
    result = re.sub(
        r"^\| BINDING_PENDING \| Exact accepted (?:feature config keys in "
        r"reconciled config\.py / manifest\.py / feature README|contribution "
        r"configuration in strict config / manifest\.ts / workflow README) \|.*$",
        PENDING_CONFIG_ROW,
        result,
        flags=re.MULTILINE,
    )
    result = result.replace("| BINDING_PENDING |", "| PHASE0_BOUND |")
    result = result.replace(
        "Import Linter and AST checks.",
        "The repository AST architecture check.",
    )
    result = result.replace(
        "Import Linter, physical removal and startup tests.",
        "The repository AST architecture check, physical removal and startup tests.",
    )
    result = result.replace("uv run --frozen lint-imports\n", "")
    result = re.sub(
        r"^\| NOT_REVALIDATED \| (`[^`]+@\d+`)",
        r"| DOCUMENTARY_BOUND | \1",
        result,
        flags=re.MULTILINE,
    )
    result = re.sub(
        r"(Feature_Requirement_Traceability_Register\.md`?\]\([^)]*\) \| `)"
        r"[a-f0-9]{40}(`)",
        rf"\g<1>{register_blob}\2",
        result,
    )
    result = re.sub(
        r"(Phased_Feature_Implementation_Plan\.md`?\]\([^)]*\) \| `)"
        r"[a-f0-9]{40}(`)",
        rf"\g<1>{plan_blob}\2",
        result,
    )
    result = re.sub(
        r"^The register records specification blob .*?$",
        "The historical specification blobs and their clause-level disposition are "
        "reconciled in `docs/dev/evidence/specification-drift.md`; the normalized "
        "205-feature register and complete dependency graph are hash-pinned by "
        "`docs/dev/evidence/baseline-manifest.json`. Documentary binding does not "
        "claim runtime acceptance for an unimplemented feature.",
        result,
        flags=re.MULTILINE,
    )
    return result


def main() -> int:
    """Write normalized READMEs or fail on generated binding drift.

    Returns:
        Process exit status: zero on success and one when drift remains.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    register_blob = _git_blob(
        REPO / "docs/dev/Feature_Requirement_Traceability_Register.md"
    )
    plan_blob = _git_blob(REPO / "docs/dev/Phased_Feature_Implementation_Plan.md")
    drift: list[str] = []
    for path in README_PATHS:
        content = path.read_text(encoding="utf-8")
        expected = normalized(_baseline_content(path), register_blob, plan_blob)
        if content == expected:
            continue
        if args.write:
            path.write_text(expected, encoding="utf-8", newline="")
            print(f"[WRITE] {path.relative_to(REPO)}")
        else:
            drift.append(path.relative_to(REPO).as_posix())
    if drift:
        print("[FAIL] domain README Phase 0 binding drift:")
        for drift_path in drift:
            print(f"  - {drift_path}")
        return 1
    print(f"[OK] {len(README_PATHS)} authoritative domain README bindings are current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
