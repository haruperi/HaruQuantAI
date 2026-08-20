"""Provider removability, lifecycle, and safety evidence enforcer.

Traces to: P16-T03, Phase 16, Gate G16
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class EvidenceViolation:
    """Represents a single detected missing evidence violation."""

    def __init__(self, code: str, path: str, line: int, target: str) -> None:
        """Initialize violation record."""
        self.code = code
        self.path = path.replace("\\", "/")
        self.line = line
        self.target = target

    def format(self) -> str:
        """Format violation into standardized one-line string.

        Returns:
            Formatted string representation.
        """
        return f"{self.code} {self.path}:{self.line} {self.target}"

    def sort_key(self) -> tuple[str, str, int, str]:
        """Return tuple key for deterministic sorting.

        Returns:
            Deterministic sorting key.
        """
        return (self.code, self.path, self.line, self.target)


def check_provider_evidence(
    matrix_data: dict[str, Any],
    repo_root: Path,
) -> list[EvidenceViolation]:
    """Verify presence of all required test and matrix evidence files.

    Args:
        matrix_data: Loaded removability matrix dictionary.
        repo_root: Repository root path.

    Returns:
        List of all detected EvidenceViolation records.
    """
    violations: list[EvidenceViolation] = []
    providers = matrix_data.get("providers", [])

    config_matrix_test = (
        repo_root / "tests" / "removability" / "test_config_disable_matrix.py"
    )
    if not config_matrix_test.is_file():
        violations.append(
            EvidenceViolation(
                "DELETION_EVIDENCE_MISSING",
                "tests/removability/test_config_disable_matrix.py",
                1,
                "Config disable matrix test missing",
            )
        )

    deletion_test = (
        repo_root / "tests" / "removability" / "test_physical_deletion_matrix.py"
    )
    if not deletion_test.is_file():
        violations.append(
            EvidenceViolation(
                "DELETION_EVIDENCE_MISSING",
                "tests/removability/test_physical_deletion_matrix.py",
                1,
                "Physical deletion test missing",
            )
        )

    reinstall_test = (
        repo_root / "tests" / "removability" / "test_required_provider_inverse.py"
    )
    if not reinstall_test.is_file():
        violations.append(
            EvidenceViolation(
                "REINSTALL_EVIDENCE_MISSING",
                "tests/removability/test_required_provider_inverse.py",
                1,
                "Inverse and reinstall safety test missing",
            )
        )

    for p in providers:
        prov_id = p.get("provider_id", "")
        domain = p.get("domain", "")

        if domain == "ui":
            ui_test_file = (
                repo_root / "tests" / "ui" / "structural" / "test_feature_registry.py"
            )
            if not ui_test_file.is_file():
                violations.append(
                    EvidenceViolation(
                        "UI_UNAVAILABLE_EVIDENCE_MISSING",
                        f"tests/ui/{prov_id}",
                        1,
                        prov_id,
                    )
                )

    return sorted(violations, key=lambda v: v.sort_key())


def run_evidence_check(
    root: Path,
    matrix_path: Path,
) -> list[EvidenceViolation]:
    """Execute complete provider evidence scan.

    Args:
        root: Repository root path.
        matrix_path: Path to removability_matrix.json.

    Returns:
        Sorted list of violations.
    """
    if not matrix_path.is_file():
        print(f"Matrix file not found: {matrix_path}", file=sys.stderr)
        sys.exit(2)

    try:
        matrix_data = json.loads(matrix_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Invalid matrix file: {exc}", file=sys.stderr)
        sys.exit(2)

    return check_provider_evidence(matrix_data, root)


def main() -> None:
    """CLI entry point for evidence enforcement."""
    parser = argparse.ArgumentParser(
        description="Enforce provider removability and safety evidence."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="Root directory of repository.",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        required=True,
        help="Path to removability_matrix.json.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    matrix = args.matrix.resolve()

    violations = run_evidence_check(root, matrix)

    if not violations:
        print("provider evidence: PASS")
        sys.exit(0)

    for v in violations:
        print(v.format())

    print(f"\nFAILURE: {len(violations)} evidence violations found.")
    sys.exit(1)


if __name__ == "__main__":
    main()
