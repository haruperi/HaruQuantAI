"""Fresh-process copied-tree physical deletion and reinstall runner.

Traces to: P11-T02, P11-T03, Gate G11
"""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.kernel.discovery import discover_manifests
from tests.removability.harness import run_in_fresh_process

_EXCLUDE_PATTERNS = (
    ".git",
    "node_modules",
    ".next",
    ".turbo",
    "dist",
    "build",
    "__pycache__",
    "*.pyc",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "artifacts",
)


def validate_delete_target(
    repo_root: Path, isolated_root: Path, target_dir: Path
) -> None:
    """Validate target path is strictly within isolated copy and never in source.

    Args:
        repo_root: Real source repository root path.
        isolated_root: Temporary copied repository root path.
        target_dir: Target provider directory to delete.

    Raises:
        ValueError: If target is in source repo or escapes isolated root.
    """
    resolved_target = target_dir.resolve()
    resolved_isolated = isolated_root.resolve()
    resolved_repo = repo_root.resolve()

    if resolved_isolated == resolved_repo:
        msg = "Refusing to operate on real repository root"
        raise ValueError(msg)

    try:
        rel_to_isolated = resolved_target.relative_to(resolved_isolated)
    except ValueError:
        msg = f"Target {target_dir} escapes isolated root {isolated_root}"
        raise ValueError(msg) from None

    if not rel_to_isolated.parts or rel_to_isolated.parts[0] != "app":
        msg = f"Target {target_dir} is not inside isolated app/ directory"
        raise ValueError(msg)


def setup_isolated_tree(repo_root: Path, isolated_root: Path) -> None:
    """Copy minimal repository tree required for isolation and deletion tests.

    Args:
        repo_root: Source repository root.
        isolated_root: Destination root path.
    """
    src_app = repo_root / "app"
    dst_app = isolated_root / "app"
    shutil.copytree(
        src_app,
        dst_app,
        ignore=shutil.ignore_patterns(*_EXCLUDE_PATTERNS),
    )

    pyproject_src = repo_root / "pyproject.toml"
    if pyproject_src.exists():
        shutil.copy2(pyproject_src, isolated_root / "pyproject.toml")

    fixtures_src = repo_root / "tests" / "removability" / "fixtures"
    if fixtures_src.exists():
        fixtures_dst = isolated_root / "tests" / "removability" / "fixtures"
        fixtures_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            fixtures_src,
            fixtures_dst,
            ignore=shutil.ignore_patterns(*_EXCLUDE_PATTERNS),
        )


def find_provider_directory(app_root: Path, provider_id: str) -> Path | None:
    """Locate on-disk provider directory matching a provider ID.

    Args:
        app_root: Application root directory to search.
        provider_id: Provider identifier.

    Returns:
        Path to the provider directory, or None if not found.
    """
    discovered = discover_manifests(app_root)
    for disc in discovered:
        if str(disc.manifest.provider_id) == provider_id:
            return disc.manifest_path.parent
    return None


def execute_deletion_test(
    repo_root: Path,
    isolated_root: Path,
    provider_id: str,
    reinstall: bool = False,
) -> dict[str, Any]:
    """Execute physical deletion and optional reinstall verification for one provider.

    Args:
        repo_root: Real repository root.
        isolated_root: Temporary copied repository root.
        provider_id: Unique provider identifier.
        reinstall: Whether to run reinstall phase after deletion.

    Returns:
        Structured test result dictionary.

    Raises:
        ValueError: If provider is not found or validation fails.
    """
    src_provider_dir = find_provider_directory(repo_root / "app", provider_id)
    if src_provider_dir is None:
        msg = f"Provider {provider_id} not found in source tree"
        raise ValueError(msg)

    rel_path = src_provider_dir.relative_to(repo_root)
    dst_provider_dir = isolated_root / rel_path

    validate_delete_target(repo_root, isolated_root, dst_provider_dir)

    # 1. Delete provider directory from isolated copy
    shutil.rmtree(dst_provider_dir)

    # 2. Fresh-process verification after deletion
    delete_script = f"""
import sys
from pathlib import Path
from app.kernel.discovery import discover_manifests

repo_root = Path({str(isolated_root.resolve())!r})
discovered = discover_manifests(repo_root / "app")
prov_ids = [str(d.manifest.provider_id) for d in discovered]
assert {provider_id!r} not in prov_ids

import app.kernel
import app.composition

for mod in list(sys.modules):
    assert {provider_id!r} not in mod
"""
    delete_res = run_in_fresh_process(
        repository_root=isolated_root,
        script=delete_script,
        timeout_seconds=20.0,
    )
    if delete_res.returncode != 0:
        return {
            "provider_id": provider_id,
            "stage": "deletion",
            "passed": False,
            "stdout": delete_res.stdout,
            "stderr": delete_res.stderr,
        }

    # 3. Optional reinstall stage
    if reinstall:
        shutil.copytree(
            src_provider_dir,
            dst_provider_dir,
            ignore=shutil.ignore_patterns(*_EXCLUDE_PATTERNS),
        )
        reinstall_script = f"""
import sys
from pathlib import Path
from app.kernel.discovery import discover_manifests

repo_root = Path({str(isolated_root.resolve())!r})
discovered = discover_manifests(repo_root / "app")
prov_ids = [str(d.manifest.provider_id) for d in discovered]
assert {provider_id!r} in prov_ids
"""
        reinstall_res = run_in_fresh_process(
            repository_root=isolated_root,
            script=reinstall_script,
            timeout_seconds=20.0,
        )
        if reinstall_res.returncode != 0:
            return {
                "provider_id": provider_id,
                "stage": "reinstall",
                "passed": False,
                "stdout": reinstall_res.stdout,
                "stderr": reinstall_res.stderr,
            }

    return {
        "provider_id": provider_id,
        "stage": "reinstall" if reinstall else "deletion",
        "passed": True,
        "stdout": delete_res.stdout,
        "stderr": "",
    }


def main() -> None:
    """CLI entry point for physical deletion and reinstall runner."""
    parser = argparse.ArgumentParser(
        description="Provider physical deletion matrix runner."
    )
    parser.add_argument(
        "--provider-id",
        type=str,
        default=None,
        help="Target single provider ID to test deletion on.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run deletion tests on all discovered optional providers.",
    )
    parser.add_argument(
        "--reinstall",
        action="store_true",
        help="Test reinstall phase after physical deletion.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional report output path.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    discovered = discover_manifests(repo_root / "app")
    target_ids: list[str] = []

    if args.provider_id:
        target_ids = [args.provider_id]
    elif args.all:
        target_ids = [str(d.manifest.provider_id) for d in discovered]
    else:
        target_ids = ["indicator.rsi.default"]

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        isolated_root = Path(tmp_dir)
        setup_isolated_tree(repo_root, isolated_root)

        for prov_id in target_ids:
            res = execute_deletion_test(
                repo_root=repo_root,
                isolated_root=isolated_root,
                provider_id=prov_id,
                reinstall=args.reinstall,
            )
            results.append(res)
            print(f"[{'PASS' if res['passed'] else 'FAIL'}] {prov_id} ({res['stage']})")

    report_text = json.dumps(results, indent=2)
    if args.report:
        args.report.write_text(report_text, encoding="utf-8")

    if any(not r["passed"] for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
