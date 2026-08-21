"""Physical-Removal Verification Tool for HaruQuantAI Features.

Validates that any feature package can be physically deleted from the codebase
without breaking compilation, type safety, quality gates, or unrelated capabilities.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class FeatureRemovalTarget:
    """Metadata for locating and removing a feature."""

    feature_id: str
    pkg_rel_path: str
    test_rel_path: str
    entry_point_name: str
    expected_missing_capability: str


TARGETS: dict[str, FeatureRemovalTarget] = {
    "FEAT-DATA-RETRIEVE_BARS": FeatureRemovalTarget(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        pkg_rel_path="app/services/data/historical_bars",
        test_rel_path="tests/services/data/historical_bars",
        entry_point_name="data-historical-bars",
        expected_missing_capability="data.historical-bars@1",
    ),
    "FEAT-BROKER-FEED_MOCK": FeatureRemovalTarget(
        feature_id="FEAT-BROKER-FEED_MOCK",
        pkg_rel_path="app/services/broker/mock_feed",
        test_rel_path="tests/services/broker/mock_feed",
        entry_point_name="broker-mock-feed",
        expected_missing_capability="broker.market-data@1",
    ),
    "FEAT-SYS-PERSIST_STORAGE": FeatureRemovalTarget(
        feature_id="FEAT-SYS-PERSIST_STORAGE",
        pkg_rel_path="app/services/system/storage",
        test_rel_path="tests/services/system/storage",
        entry_point_name="system-persist-storage",
        expected_missing_capability="system.storage@1",
    ),
}


def run_cmd(
    cmd: list[str], cwd: Path, step_name: str
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command and print execution summary.

    Args:
        cmd: Command and arguments.
        cwd: Working directory.
        step_name: Descriptive step label.

    Returns:
        CompletedProcess instance.

    Raises:
        RuntimeError: If subprocess returns non-zero exit code.
    """
    print(f"--> Running {step_name}: {' '.join(cmd)}")
    res = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        print(f"[FAIL] {step_name} failed with code {res.returncode}:\n")
        print(res.stdout)
        print(res.stderr)
        msg = f"Step '{step_name}' failed with exit code {res.returncode}"
        raise RuntimeError(msg)
    print(f"[OK] {step_name} passed.\n")
    return res


def remove_feature_from_pyproject(pyproject_path: Path, entry_point_name: str) -> None:
    """Remove entry point registration from pyproject.toml."""
    content = pyproject_path.read_text(encoding="utf-8")
    pattern = rf"^{re.escape(entry_point_name)}\s*=.*$\n?"
    new_content = re.sub(pattern, "", content, flags=re.MULTILINE)
    pyproject_path.write_text(new_content, encoding="utf-8")


def remove_feature_from_importlinter(linter_path: Path, pkg_rel_path: str) -> None:
    """Remove package module from .importlinter if present."""
    if not linter_path.exists():
        return
    mod_name = pkg_rel_path.replace("/", ".")
    content = linter_path.read_text(encoding="utf-8")
    new_lines = [line for line in content.splitlines() if mod_name not in line]
    linter_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def verify_feature_removal(target: FeatureRemovalTarget) -> bool:
    """Execute complete physical removal verification workflow in temporary isolation.

    Args:
        target: Target feature specification.

    Returns:
        True if all quality checks and runtime assertions pass, False otherwise.
    """
    print("================================================================")
    print(f"Physical-Removal Verification for Feature: {target.feature_id}")
    print("================================================================\n")

    with tempfile.TemporaryDirectory(prefix="haru_removal_") as temp_dir:
        temp_path = Path(temp_dir)
        print(f"1. Copying workspace to isolated directory: {temp_path}...")

        def ignore_patterns(_path: str, names: list[str]) -> set[str]:
            return {
                ".git",
                ".venv",
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "htmlcov",
                ".coverage",
            }.intersection(names)

        shutil.copytree(ROOT_DIR, temp_path, dirs_exist_ok=True, ignore=ignore_patterns)

        # 2. Physically remove feature package
        pkg_full_path = temp_path / target.pkg_rel_path
        if pkg_full_path.exists():
            print(f"2. Deleting feature package directory: {pkg_full_path}...")
            shutil.rmtree(pkg_full_path)

        # 3. Physically remove feature-local tests
        test_full_path = temp_path / target.test_rel_path
        if test_full_path.exists():
            print(f"3. Deleting feature-local tests: {test_full_path}...")
            shutil.rmtree(test_full_path)

        # Remove multi-feature integration tests importing deleted feature
        multi_feat_tests = [
            temp_path / "tests/services/test_vertical_feature_pair.py",
            temp_path / "tests/services/test_lifecycle_leak.py",
            temp_path / "tests/api/test_facade.py",
        ]
        for mft in multi_feat_tests:
            if mft.exists():
                mft.unlink()

        # 4. Remove entry point declaration from pyproject.toml & .importlinter
        print("4. Updating pyproject.toml and .importlinter...")
        remove_feature_from_pyproject(
            temp_path / "pyproject.toml", target.entry_point_name
        )
        remove_feature_from_importlinter(
            temp_path / ".importlinter", target.pkg_rel_path
        )

        # 5. Run static lint and format checks
        run_cmd(
            ["uv", "run", "ruff", "format", "--check", "."],
            temp_path,
            "Ruff Format Check",
        )
        run_cmd(
            ["uv", "run", "ruff", "check", "."],
            temp_path,
            "Ruff Lint Check",
        )

        # 6. Run type check
        run_cmd(["uv", "run", "mypy"], temp_path, "Mypy Type Check")

        # 7. Run Import Linter
        run_cmd(["uv", "run", "lint-imports"], temp_path, "Import Linter Check")

        # 8. Run Architectural AST Check
        run_cmd(
            ["uv", "run", "python", "scripts/architecture_check.py"],
            temp_path,
            "Architectural AST Invariant Check",
        )

        # 9. Run Remaining Core Test Suite
        run_cmd(
            [
                "uv",
                "run",
                "pytest",
                "-k",
                "not test_discovered_features_non_empty",
            ],
            temp_path,
            "Core Test Suite",
        )

        # 10. Run Application Runtime Degradation Assertion
        print("10. Testing runtime graceful degradation with feature absent...")
        verification_script = f"""
import asyncio
from app.composition.engine import CompositionEngine

async def main():
    engine = CompositionEngine()
    stale_config = \"\"\"
    [profile]
    name = "research"
    [features.{target.feature_id}]
    enabled = true
    \"\"\"
    await engine.load_and_reconcile_toml(stale_config)
    status = engine.get_status()
    assert "{target.feature_id}" not in status.active_features, (
        f"Feature {target.feature_id} must not be active"
    )
    assert not engine.registry.is_available("{target.expected_missing_capability}"), (
        f"Capability {target.expected_missing_capability} should be absent"
    )
    print("Runtime degradation verification succeeded!")

asyncio.run(main())
"""
        run_cmd(
            ["uv", "run", "python", "-c", verification_script],
            temp_path,
            "Runtime Degradation Verification",
        )

    print("\n================================================================")
    print(f"[SUCCESS] Feature {target.feature_id} is 100% physically removable!")
    print("================================================================\n")
    return True


def main() -> int:
    """CLI entry point.

    Returns:
        0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Verify physical removability of a feature."
    )
    parser.add_argument(
        "feature_id",
        choices=list(TARGETS.keys()),
        help="Feature ID to test physical removal for.",
    )
    args = parser.parse_args()

    target = TARGETS[args.feature_id]
    try:
        success = verify_feature_removal(target)
        return 0 if success else 1
    except RuntimeError as e:
        print(f"\n[FATAL] Removal verification failed: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
