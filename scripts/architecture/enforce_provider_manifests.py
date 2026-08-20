"""Provider manifest and dependency graph integrity enforcer.

Traces to: P16-T02, Phase 16, Gate G16
"""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.kernel.discovery import DiscoveredProvider, discover_manifests
from app.kernel.errors import ResolutionError
from app.kernel.identifiers import ProviderId
from app.kernel.resolver import resolve_providers


class ManifestViolation:
    """Represents a single detected manifest or resolution violation."""

    def __init__(self, code: str, path: str, line: int, target: str) -> None:
        """Initialize violation record."""
        self.code = code
        self.path = path.replace("\\", "/")
        self.line = line
        self.target = target

    def format(self) -> str:
        """Format violation into standardized one-line string.

        Returns:
            Formatted violation string.
        """
        return f"{self.code} {self.path}:{self.line} {self.target}"

    def sort_key(self) -> tuple[str, str, int, str]:
        """Return tuple key for deterministic sorting.

        Returns:
            Sorting key tuple.
        """
        return (self.code, self.path, self.line, self.target)


def check_manifests_integrity(
    discovered: tuple[DiscoveredProvider, ...] | list[DiscoveredProvider],
    matrix_data: dict[str, Any],
    repo_root: Path,
) -> list[ManifestViolation]:
    """Verify provider manifests, specs, resolution, and cycle absence.

    Args:
        discovered: List of DiscoveredManifest items discovered on disk.
        matrix_data: Loaded removability matrix dictionary.
        repo_root: Repository root path.

    Returns:
        List of all detected ManifestViolation records.
    """
    _ = matrix_data
    violations: list[ManifestViolation] = []
    seen_providers: dict[ProviderId, DiscoveredProvider] = {}

    for disc in discovered:
        pid = disc.manifest.provider_id
        rel_path = str(disc.manifest_path.relative_to(repo_root)).replace("\\", "/")

        # 1. Duplicate check
        if pid in seen_providers:
            violations.append(
                ManifestViolation(
                    "PROVIDER_MANIFEST_DUPLICATE",
                    rel_path,
                    1,
                    str(pid),
                )
            )
        seen_providers[pid] = disc

        # 2. Spec existence check
        for prov_cap in disc.manifest.provides:
            cap_domain = prov_cap.capability_id.domain
            cap_name = prov_cap.capability_id.capability
            cap_major = prov_cap.capability_id.major
            spec_file = (
                repo_root
                / "app"
                / "capabilities"
                / cap_domain
                / f"{cap_name}"
                / f"v{cap_major}.py"
            )
            spec_file_alt = (
                repo_root / "app" / "capabilities" / cap_domain / f"v{cap_major}.py"
            )
            if not spec_file.exists() and not spec_file_alt.exists():
                violations.append(
                    ManifestViolation(
                        "CAPABILITY_SPEC_MISSING",
                        rel_path,
                        1,
                        str(prov_cap.capability_id),
                    )
                )

    # 3. Graph resolution and cycle check
    all_manifests = tuple(d.manifest for d in discovered)
    enabled_ids = frozenset(d.manifest.provider_id for d in discovered)

    try:
        resolve_providers(
            all_manifests,
            enabled_provider_ids=enabled_ids,
            selected_provider_ids={},
        )
    except ResolutionError as exc:
        violations.append(
            ManifestViolation(
                "HARD_DEPENDENCY_CYCLE",
                "app/kernel/resolver.py",
                1,
                str(exc),
            )
        )

    return sorted(violations, key=lambda v: v.sort_key())


def run_manifest_check(
    root: Path,
    matrix_path: Path,
) -> list[ManifestViolation]:
    """Execute complete manifest and resolution integrity check.

    Args:
        root: Root directory of repository.
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

    discovered = discover_manifests(root / "app")
    return check_manifests_integrity(discovered, matrix_data, root)


def main() -> None:
    """CLI entry point for manifest integrity enforcement."""
    parser = argparse.ArgumentParser(
        description="Enforce provider manifest graph integrity."
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

    violations = run_manifest_check(root, matrix)

    if not violations:
        print("provider manifests: PASS")
        sys.exit(0)

    for v in violations:
        print(v.format())

    print(f"\nFAILURE: {len(violations)} manifest integrity violations found.")
    sys.exit(1)


if __name__ == "__main__":
    main()
