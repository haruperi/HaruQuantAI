"""Physical-Removal Verification Tool for HaruQuantAI Features.

Validates that any feature package can be physically deleted from the codebase
without breaking compilation, type safety, quality gates, or unrelated capabilities.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MIN_MODULE_PARTS_FOR_FEATURE_DIR = 2


@dataclass(frozen=True, slots=True)
class FeatureRemovalTarget:
    """Metadata for locating and removing a feature."""

    feature_id: str
    pkg_rel_path: str
    test_rel_path: str
    entry_point_name: str
    provided_capabilities: list[str]


@dataclass(slots=True)
class StepResult:
    """Diagnostic result of a single verification step."""

    step_name: str
    passed: bool
    elapsed_seconds: float
    error_message: str | None = None


@dataclass(slots=True)
class TargetVerificationReport:
    """Verification results for one feature target."""

    feature_id: str
    entry_point_name: str
    pkg_rel_path: str
    test_rel_path: str
    provided_capabilities: list[str]
    passed: bool
    elapsed_seconds: float
    steps: list[StepResult] = field(default_factory=list)


@dataclass(slots=True)
class OverallRemovabilityReport:
    """Complete multi-feature removability report schema."""

    timestamp: str
    overall_passed: bool
    total_elapsed_seconds: float
    targets: list[TargetVerificationReport] = field(default_factory=list)


def discover_targets(root_dir: Path) -> dict[str, FeatureRemovalTarget]:
    """Dynamically discover feature removal targets from pyproject.toml.

    Args:
        root_dir: Root directory of the repository.

    Returns:
        Dictionary mapping feature ID to FeatureRemovalTarget.

    Raises:
        FileNotFoundError: If pyproject.toml is missing.
    """
    pyproject_file = root_dir / "pyproject.toml"
    if not pyproject_file.exists():
        msg = f"pyproject.toml not found in {root_dir}"
        raise FileNotFoundError(msg)

    with pyproject_file.open("rb") as f:
        data = tomllib.load(f)

    entry_points = (
        data.get("project", {}).get("entry-points", {}).get("haruquantai.features", {})
    )

    targets: dict[str, FeatureRemovalTarget] = {}

    for ep_name, ep_target in entry_points.items():
        if ":" not in ep_target:
            continue
        mod_str, func_str = ep_target.split(":", 1)

        # Resolve module package directory
        parts = mod_str.split(".")
        pkg_parts = (
            parts[:-1]
            if len(parts) >= MIN_MODULE_PARTS_FOR_FEATURE_DIR and parts[-1] == "feature"
            else parts
        )
        pkg_rel_path = "/".join(pkg_parts)

        # Infer test path: app/services/x/y -> tests/services/x/y
        test_parts = ["tests", *pkg_parts[1:]]
        test_rel_path = "/".join(test_parts)

        try:
            mod = import_module(mod_str)
            factory = getattr(mod, func_str)
            feat = factory() if callable(factory) else factory
            spec = getattr(feat, "spec", None)
            if spec is None:
                continue

            feature_id = spec.feature_id
            provided_caps = [cap.identifier for cap in spec.provides]

            targets[feature_id] = FeatureRemovalTarget(
                feature_id=feature_id,
                pkg_rel_path=pkg_rel_path,
                test_rel_path=test_rel_path,
                entry_point_name=ep_name,
                provided_capabilities=provided_caps,
            )
        except (ImportError, AttributeError, ValueError) as err:
            print(f"[WARN] Could not dynamically load target '{ep_name}': {err}")

    return targets


def run_step(
    cmd: list[str], cwd: Path, step_name: str
) -> tuple[bool, float, str | None]:
    """Run a subprocess command and record timing and errors.

    Args:
        cmd: Command argument list.
        cwd: Current working directory.
        step_name: Descriptive name of the step.

    Returns:
        Tuple of (passed, elapsed_seconds, error_message).
    """
    print(f"--> Running {step_name}: {' '.join(cmd)}")
    start_t = time.time()
    res = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = round(time.time() - start_t, 2)

    if res.returncode != 0:
        print(f"[FAIL] {step_name} failed with code {res.returncode} ({elapsed}s):\n")
        output = (res.stdout or "") + "\n" + (res.stderr or "")
        print(output.strip())
        return False, elapsed, output.strip()

    print(f"[OK] {step_name} passed in {elapsed}s.\n")
    return True, elapsed, None


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


def verify_target(target: FeatureRemovalTarget) -> TargetVerificationReport:
    """Verify physical removability of one feature target in an isolated workspace.

    Args:
        target: Target feature specification.

    Returns:
        TargetVerificationReport with step results and timing.
    """
    print("================================================================")
    print(f"Physical-Removal Verification for Feature: {target.feature_id}")
    print(f"Package: {target.pkg_rel_path}")
    print(f"Tests: {target.test_rel_path}")
    print(f"Capabilities: {target.provided_capabilities}")
    print("================================================================\n")

    start_target_time = time.time()
    steps: list[StepResult] = []
    overall_target_pass = True

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

        verification_steps: list[tuple[list[str], str]] = [
            (["uv", "run", "ruff", "format", "--check", "."], "Ruff Format Check"),
            (["uv", "run", "ruff", "check", "."], "Ruff Lint Check"),
            (["uv", "run", "mypy"], "Mypy Type Check"),
            (["uv", "run", "lint-imports"], "Import Linter Check"),
            (
                ["uv", "run", "python", "scripts/architecture_check.py"],
                "Architectural AST Invariant Check",
            ),
            (
                [
                    "uv",
                    "run",
                    "pytest",
                    "-k",
                    "not test_discovered_features_non_empty",
                ],
                "Core & Unrelated Feature Test Suite",
            ),
        ]

        for cmd, name in verification_steps:
            passed, elapsed, err = run_step(cmd, temp_path, name)
            steps.append(
                StepResult(
                    step_name=name,
                    passed=passed,
                    elapsed_seconds=elapsed,
                    error_message=err,
                )
            )
            if not passed:
                overall_target_pass = False
                break

        # Runtime degradation verification script if static checks and core tests pass
        if overall_target_pass:
            first_cap = (
                target.provided_capabilities[0]
                if target.provided_capabilities
                else "dummy.cap@1"
            )
            runtime_script = f"""
import asyncio
from app.composition.engine import CompositionEngine
from app.api.facade import create_api
from app.kernel.capability import CapabilityUnavailableError

async def main():
    engine = CompositionEngine()
    stale_config = \"\"\"
    [application]
    profile = "research"
    [features.{target.feature_id}]
    enabled = true
    \"\"\"
    await engine.load_and_reconcile_toml(stale_config)
    status = engine.get_status()
    assert "{target.feature_id}" not in status.active_features, (
        f"Feature '{target.feature_id}' must not be active when physically removed"
    )
    assert not engine.registry.is_available("{first_cap}"), (
        f"Capability '{first_cap}' must be unavailable"
    )
    api = create_api(engine=engine)
    assert api is not None
    await engine.shutdown()
    print("Runtime degradation verification passed successfully!")

asyncio.run(main())
"""
            passed, elapsed, err = run_step(
                ["uv", "run", "python", "-c", runtime_script],
                temp_path,
                "Runtime Graceful Degradation Assertion",
            )
            steps.append(
                StepResult(
                    step_name="Runtime Graceful Degradation Assertion",
                    passed=passed,
                    elapsed_seconds=elapsed,
                    error_message=err,
                )
            )
            if not passed:
                overall_target_pass = False

    target_elapsed = round(time.time() - start_target_time, 2)
    return TargetVerificationReport(
        feature_id=target.feature_id,
        entry_point_name=target.entry_point_name,
        pkg_rel_path=target.pkg_rel_path,
        test_rel_path=target.test_rel_path,
        provided_capabilities=target.provided_capabilities,
        passed=overall_target_pass,
        elapsed_seconds=target_elapsed,
        steps=steps,
    )


def main() -> int:
    """CLI entry point supporting --all, --feature, and --report.

    Returns:
        0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Verify physical removability of HaruQuantAI feature packages."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run physical removal verification for all registered features.",
    )
    parser.add_argument(
        "--feature",
        type=str,
        default=None,
        help="Specific feature ID to verify physical removal for.",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Path to write the JSON removability report.",
    )
    args = parser.parse_args()

    targets = discover_targets(ROOT_DIR)
    if not targets:
        print("[ERROR] No feature targets discovered from pyproject.toml.")
        return 1

    targets_to_verify: list[FeatureRemovalTarget] = []
    if args.feature:
        if args.feature not in targets:
            known = list(targets.keys())
            print(f"[ERROR] Target feature '{args.feature}' not found in {known}")
            return 1
        targets_to_verify.append(targets[args.feature])
    elif args.all or not sys.argv[1:]:
        targets_to_verify = list(targets.values())
    else:
        parser.print_help()
        return 1

    start_total_time = time.time()
    target_reports: list[TargetVerificationReport] = []
    all_passed = True

    for target in targets_to_verify:
        report = verify_target(target)
        target_reports.append(report)
        if not report.passed:
            all_passed = False

    total_elapsed = round(time.time() - start_total_time, 2)
    overall_report = OverallRemovabilityReport(
        timestamp=datetime.now(UTC).isoformat(),
        overall_passed=all_passed,
        total_elapsed_seconds=total_elapsed,
        targets=target_reports,
    )

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(asdict(overall_report), indent=2), encoding="utf-8"
        )
        print(f"\n[INFO] Removability report written to: {report_path.resolve()}")

    print("\n================================================================")
    print("Physical-Removal Verification Summary")
    print("================================================================")
    for tr in target_reports:
        mark = "[PASS]" if tr.passed else "[FAIL]"
        print(f"  {mark} {tr.feature_id} in {tr.elapsed_seconds}s")
    print(f"\nTotal elapsed: {total_elapsed}s")
    summary_msg = (
        "[SUCCESS] All features verified physically removable!"
        if all_passed
        else "[FAILURE] One or more features failed removal verification."
    )
    print(f"Overall result: {summary_msg}")
    print("================================================================\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
