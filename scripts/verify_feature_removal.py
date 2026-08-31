#!/usr/bin/env python
"""Physically delete registered features and verify graceful degradation."""

from __future__ import annotations

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
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class FeatureRemovalTarget:
    """Resolved source, test, contract, and dependency metadata for one feature."""

    feature_id: str
    pkg_rel_path: str
    test_rel_path: str
    entry_point_name: str
    provided_capabilities: tuple[str, ...]
    required_consumers: tuple[str, ...] = ()
    consumer_capabilities: tuple[str, ...] = ()
    unrelated_features: tuple[str, ...] = ()


@dataclass(slots=True)
class StepResult:
    """Outcome of one removal-verification command."""

    step_name: str
    passed: bool
    elapsed_seconds: float
    error_message: str | None = None


@dataclass(slots=True)
class TargetVerificationReport:
    """Complete verification evidence for one removed feature."""

    feature_id: str
    entry_point_name: str
    pkg_rel_path: str
    test_rel_path: str
    provided_capabilities: tuple[str, ...]
    required_consumers: tuple[str, ...]
    unrelated_features: tuple[str, ...]
    passed: bool
    elapsed_seconds: float
    steps: list[StepResult] = field(default_factory=list)


@dataclass(slots=True)
class OverallRemovabilityReport:
    """Machine-readable removal matrix report."""

    timestamp: str
    overall_passed: bool
    total_elapsed_seconds: float
    targets: list[TargetVerificationReport] = field(default_factory=list)


def _entry_points(root_dir: Path) -> dict[str, str]:
    with (root_dir / "pyproject.toml").open("rb") as file:
        data = tomllib.load(file)
    value = (
        data.get("project", {}).get("entry-points", {}).get("haruquantai.features", {})
    )
    if not isinstance(value, dict):
        raise TypeError("[project.entry-points.'haruquantai.features'] is invalid")
    return {str(name): str(target) for name, target in value.items()}


def discover_targets(root_dir: Path) -> dict[str, FeatureRemovalTarget]:
    """Discover every registered feature or fail on incomplete metadata.

    Returns:
        Complete feature-removal target mapping.

    Raises:
        RuntimeError: If an entry point cannot be resolved or is duplicated.
        TypeError: If entry-point metadata has an invalid type.
    """
    loaded: dict[str, tuple[str, str, Any]] = {}
    for entry_point_name, target in _entry_points(root_dir).items():
        if ":" not in target:
            msg = f"Entry point '{entry_point_name}' has invalid target '{target}'"
            raise RuntimeError(msg)
        module_name, factory_name = target.split(":", maxsplit=1)
        try:
            module = import_module(module_name)
            factory = getattr(module, factory_name)
            feature = factory() if callable(factory) else factory
            spec = feature.spec
            spec.validate()
        except Exception as error:
            msg = f"Failed to resolve feature entry point '{entry_point_name}': {error}"
            raise RuntimeError(msg) from error

        feature_id = str(spec.feature_id)
        if feature_id in loaded:
            other_entry_point = loaded[feature_id][0]
            msg = (
                f"Duplicate feature ID '{feature_id}' from '{other_entry_point}' "
                f"and '{entry_point_name}'"
            )
            raise RuntimeError(msg)
        loaded[feature_id] = (entry_point_name, module_name, spec)

    targets: dict[str, FeatureRemovalTarget] = {}
    all_feature_ids = set(loaded)
    for feature_id, (entry_point_name, module_name, spec) in loaded.items():
        module_parts = module_name.split(".")
        package_parts = (
            module_parts[:-1] if module_parts[-1] == "feature" else module_parts
        )
        package_path = "/".join(package_parts)
        test_path = "/".join(("tests", *package_parts[1:]))
        provided = {capability.identifier for capability in spec.provides}

        consumers: set[str] = set()
        frontier = {feature_id}
        while frontier:
            upstream_capabilities = {
                capability.identifier
                for upstream_id in frontier
                for capability in loaded[upstream_id][2].provides
            }
            next_frontier = {
                candidate_id
                for candidate_id, (_ep, _module, candidate_spec) in loaded.items()
                if candidate_id not in consumers
                and candidate_id != feature_id
                and any(
                    capability.identifier in upstream_capabilities
                    for capability in candidate_spec.requires
                )
            }
            consumers.update(next_frontier)
            frontier = next_frontier

        consumer_capabilities = {
            capability.identifier
            for consumer_id in consumers
            for capability in loaded[consumer_id][2].provides
        }
        unrelated = all_feature_ids - consumers - {feature_id}
        targets[feature_id] = FeatureRemovalTarget(
            feature_id=feature_id,
            pkg_rel_path=package_path,
            test_rel_path=test_path,
            entry_point_name=entry_point_name,
            provided_capabilities=tuple(sorted(provided)),
            required_consumers=tuple(sorted(consumers)),
            consumer_capabilities=tuple(sorted(consumer_capabilities)),
            unrelated_features=tuple(sorted(unrelated)),
        )
    if not targets:
        raise RuntimeError("No registered features were discovered")
    return targets


def run_step(
    command: list[str],
    cwd: Path,
    step_name: str,
) -> StepResult:
    """Run one verification step and capture its output on failure.

    Returns:
        Captured verification-step result.
    """
    print(f"--> {step_name}: {' '.join(command)}")
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = round(time.monotonic() - started, 2)
    if result.returncode == 0:
        print(f"[OK] {step_name} ({elapsed}s)")
        return StepResult(step_name, True, elapsed)
    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )
    print(f"[FAIL] {step_name} ({elapsed}s)\n{output}")
    return StepResult(step_name, False, elapsed, output)


def _remove_importing_tests(workspace: Path, pkg_rel_path: str) -> None:
    """Delete sandbox test files that import the removed feature package.

    A physical removal takes a feature's importing tests with it; the
    isolated verification workspace must mirror that so its quality gates
    check a truthful post-removal tree. The real repository is untouched.

    Args:
        workspace: Isolated verification workspace root.
        pkg_rel_path: Feature package path relative to the repository root.
    """
    module_prefix = pkg_rel_path.replace("/", ".")
    tests_root = workspace / "tests"
    if not tests_root.is_dir():
        return
    for candidate in sorted(tests_root.rglob("*.py")):
        try:
            content = candidate.read_text(encoding="utf-8")
        except OSError:
            continue
        if f"from {module_prefix}" in content or f"import {module_prefix}" in content:
            candidate.unlink()


def remove_entry_point(pyproject_path: Path, entry_point_name: str) -> None:
    """Remove one exact feature entry-point declaration.

    Matches both quoted and unquoted TOML keys; dotted keys such as
    "workspace.runtime_configuration" are always quoted in TOML.

    Raises:
        RuntimeError: If exactly one matching declaration is not removed.
    """
    content = pyproject_path.read_text(encoding="utf-8")
    pattern = rf'^"?{re.escape(entry_point_name)}"?\s*=.*$\n?'
    updated, count = re.subn(pattern, "", content, flags=re.MULTILINE)
    if count != 1:
        msg = f"Expected one entry point named '{entry_point_name}', removed {count}"
        raise RuntimeError(msg)
    pyproject_path.write_text(updated, encoding="utf-8")


def remove_import_linter_module(linter_path: Path, package_path: str) -> None:
    """Remove the deleted feature from the generated independence list."""
    if not linter_path.exists():
        return
    module_name = package_path.replace("/", ".")
    lines = [
        line
        for line in linter_path.read_text(encoding="utf-8").splitlines()
        if module_name not in line
    ]
    linter_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _verification_profile(target: FeatureRemovalTarget) -> str:
    impacted = set(target.provided_capabilities) | set(target.consumer_capabilities)
    return "research" if "data.historical-bars@1" in impacted else "offline"


def _stale_config(
    targets: dict[str, FeatureRemovalTarget],
    target: FeatureRemovalTarget,
) -> str:
    lines = [
        "[application]",
        f'profile = "{_verification_profile(target)}"',
        "",
    ]
    for feature_id in sorted(targets):
        lines.extend(
            (
                f'[features."{feature_id}"]',
                "enabled = true",
                "",
            )
        )
    return "\n".join(lines)


def _runtime_script(
    target: FeatureRemovalTarget,
    config_path: Path,
) -> str:
    target_json = json.dumps(asdict(target))
    config_json = json.dumps(str(config_path))
    expected_ready = _verification_profile(target) == "offline"
    return f"""
import asyncio
import json
from app.composition.engine import CompositionEngine
from app.kernel.feature import FeatureState

target = json.loads({target_json!r})
config_path = {config_json}

async def main():
    baseline_tasks = {{
        task
        for task in asyncio.all_tasks()
        if task is not asyncio.current_task()
    }}
    engine = CompositionEngine()
    await engine.load_and_reconcile_file(config_path)
    status = engine.get_status()
    assert status.feature_states[target["feature_id"]] == FeatureState.MISSING
    assert target["feature_id"] not in status.active_features
    for capability in target["provided_capabilities"]:
        assert not engine.registry.is_available(capability)
    for consumer in target["required_consumers"]:
        assert status.feature_states[consumer] == FeatureState.BLOCKED
        assert consumer not in status.active_features
    for capability in target["consumer_capabilities"]:
        assert not engine.registry.is_available(capability)
    for unrelated in target["unrelated_features"]:
        assert status.feature_states[unrelated] == FeatureState.ACTIVE
        assert unrelated in status.active_features
    assert status.is_ready is {expected_ready!r}
    await engine.shutdown()
    assert not engine.reconciler.active_features
    assert not engine.registry.active_capabilities()
    assert engine.event_bus.listener_count() == 0
    await asyncio.sleep(0)
    remaining = {{
        task
        for task in asyncio.all_tasks()
        if task is not asyncio.current_task()
    }}
    assert remaining.issubset(baseline_tasks), remaining - baseline_tasks

asyncio.run(main())
"""


def _cli_script(config_path: Path, target: FeatureRemovalTarget) -> str:
    target_json = json.dumps(asdict(target))
    expected_ready = _verification_profile(target) == "offline"
    return f"""
import json
import shutil
import subprocess

target = json.loads({target_json!r})
command = shutil.which("haruquantai")
assert command is not None, "Installed haruquantai command was not found"
result = subprocess.run(
    [command, "--config", {str(config_path)!r}, "--status"],
    check=False,
    capture_output=True,
    text=True,
)
assert result.returncode == 0, result.stderr
payload = json.loads(result.stdout)
assert target["feature_id"] not in payload["active_features"]
assert payload["feature_states"][target["feature_id"]] == "MISSING"
for consumer in target["required_consumers"]:
    assert payload["feature_states"][consumer] == "BLOCKED"
    assert consumer not in payload["active_features"]
for unrelated in target["unrelated_features"]:
    assert payload["feature_states"][unrelated] == "ACTIVE"
    assert unrelated in payload["active_features"]
assert payload["is_ready"] is {expected_ready!r}
"""


def verify_target(
    target: FeatureRemovalTarget,
    all_targets: dict[str, FeatureRemovalTarget],
) -> TargetVerificationReport:
    """Verify one feature deletion inside an isolated temporary workspace.

    Returns:
        Complete target verification report.

    Raises:
        RuntimeError: If target source or metadata is inconsistent.
    """
    started = time.monotonic()
    steps: list[StepResult] = []
    passed = True

    with tempfile.TemporaryDirectory(prefix="haru_removal_") as temp_dir:
        workspace = Path(temp_dir)

        def ignored(_path: str, names: list[str]) -> set[str]:
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

        shutil.copytree(ROOT_DIR, workspace, dirs_exist_ok=True, ignore=ignored)
        package_path = workspace / target.pkg_rel_path
        test_path = workspace / target.test_rel_path
        if not package_path.is_dir():
            msg = f"Feature package does not exist: {package_path}"
            raise RuntimeError(msg)
        shutil.rmtree(package_path)
        if test_path.exists():
            shutil.rmtree(test_path)
        _remove_importing_tests(workspace, target.pkg_rel_path)

        remove_entry_point(
            workspace / "pyproject.toml",
            target.entry_point_name,
        )
        remove_import_linter_module(
            workspace / ".importlinter",
            target.pkg_rel_path,
        )
        config_path = workspace / "removal-stale.toml"
        config_path.write_text(
            _stale_config(all_targets, target),
            encoding="utf-8",
        )

        commands = [
            (["uv", "sync", "--frozen", "--dev"], "Environment sync"),
            (["uv", "run", "ruff", "format", "--check", "."], "Ruff format"),
            (["uv", "run", "ruff", "check", "."], "Ruff lint"),
            (["uv", "run", "mypy"], "Mypy"),
            (["uv", "run", "lint-imports"], "Import Linter"),
            (
                ["uv", "run", "python", "scripts/architecture_check.py"],
                "Architecture AST",
            ),
            (
                ["uv", "run", "python", "scripts/validate_feature_docs.py"],
                "Feature documentation",
            ),
            (["uv", "run", "pytest", "--no-cov"], "Complete remaining test suite"),
            (
                [
                    "uv",
                    "run",
                    "python",
                    "-c",
                    _runtime_script(target, config_path),
                ],
                "MISSING/BLOCKED/unrelated ACTIVE and leak assertions",
            ),
            (
                [
                    "uv",
                    "run",
                    "python",
                    "-c",
                    _cli_script(config_path, target),
                ],
                "Installed application status command",
            ),
        ]
        for command, name in commands:
            result = run_step(command, workspace, name)
            steps.append(result)
            if not result.passed:
                passed = False
                break

    return TargetVerificationReport(
        feature_id=target.feature_id,
        entry_point_name=target.entry_point_name,
        pkg_rel_path=target.pkg_rel_path,
        test_rel_path=target.test_rel_path,
        provided_capabilities=target.provided_capabilities,
        required_consumers=target.required_consumers,
        unrelated_features=target.unrelated_features,
        passed=passed,
        elapsed_seconds=round(time.monotonic() - started, 2),
        steps=steps,
    )


def main() -> int:
    """Run one target or the complete registered-feature removal matrix.

    Returns:
        Zero when every selected target passes; otherwise one.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--feature", type=str, default=None)
    parser.add_argument("--report", type=str, default=None)
    args = parser.parse_args()

    try:
        targets = discover_targets(ROOT_DIR)
    except (RuntimeError, TypeError) as error:
        print(f"[ERROR] {error}")
        return 1

    if args.feature is not None:
        target = targets.get(args.feature)
        if target is None:
            print(f"[ERROR] Unknown feature '{args.feature}'. Known: {sorted(targets)}")
            return 1
        selected = [target]
    elif args.all or not sys.argv[1:]:
        selected = [targets[feature_id] for feature_id in sorted(targets)]
    else:
        parser.print_help()
        return 1

    started = time.monotonic()
    reports: list[TargetVerificationReport] = []
    for target in selected:
        print(f"\n=== Removing {target.feature_id} ===")
        reports.append(verify_target(target, targets))

    overall = OverallRemovabilityReport(
        timestamp=datetime.now(UTC).isoformat(),
        overall_passed=all(report.passed for report in reports),
        total_elapsed_seconds=round(time.monotonic() - started, 2),
        targets=reports,
    )
    if args.report is not None:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(asdict(overall), indent=2),
            encoding="utf-8",
        )
    for report in reports:
        marker = "PASS" if report.passed else "FAIL"
        print(f"[{marker}] {report.feature_id} ({report.elapsed_seconds}s)")
    return 0 if overall.overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
