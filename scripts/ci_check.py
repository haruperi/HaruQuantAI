#!/usr/bin/env python
"""Profile-driven validation entry point for HaruQuantAI."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

from scripts.validation_router import (
    PUBLIC_PROFILES,
    RoutingDecision,
    RoutingError,
    route_validation,
)

REPO: Final[Path] = Path(__file__).resolve().parents[1]
UI_ROOT: Final[Path] = REPO / "app" / "ui"


@dataclass(frozen=True)
class ValidationStep:
    """One executable validation command."""

    step_id: str
    name: str
    arguments: tuple[str, ...]
    working_directory: Path = REPO
    locked_python: bool = True

    def command(self) -> tuple[str, ...]:
        """Return the exact platform command for this step."""
        if self.locked_python:
            return ("uv", "run", "--locked", *self.arguments)
        executable = self.arguments[0]
        resolved = shutil.which(executable)
        if resolved is None and os.name == "nt" and executable == "npm":
            resolved = shutil.which("npm.cmd")
        return (resolved or executable, *self.arguments[1:])


@dataclass(frozen=True)
class StepResult:
    """Observed result of one validation command."""

    step_id: str
    name: str
    command: tuple[str, ...]
    working_directory: str
    duration_seconds: float
    exit_code: int


def _step(
    step_id: str,
    name: str,
    *arguments: str,
    working_directory: Path = REPO,
    locked_python: bool = True,
) -> ValidationStep:
    """Construct one immutable validation step.

    Returns:
        Configured validation step.
    """
    return ValidationStep(
        step_id=step_id,
        name=name,
        arguments=arguments,
        working_directory=working_directory,
        locked_python=locked_python,
    )


def _quality_steps() -> list[ValidationStep]:
    """Return repository-wide Python formatting and lint checks."""
    return [
        _step("ruff-format", "Ruff format check", "ruff", "format", "--check", "."),
        _step("ruff-lint", "Ruff lint check", "ruff", "check", "."),
    ]


def _documentation_steps() -> list[ValidationStep]:
    """Return deterministic documentation and binding checks."""
    return [
        _step(
            "feature-docs",
            "Feature documentation check",
            "python",
            "scripts/validate_feature_docs.py",
        )
    ]


def _python_steps() -> list[ValidationStep]:
    """Return comprehensive Python/product validation steps."""
    steps = [
        *_quality_steps(),
        _step("mypy", "Mypy type check", "mypy"),
        _step(
            "contracts",
            "Contract generation check",
            "python",
            "scripts/generate_contracts.py",
            "--check",
        ),
        _step(
            "architecture",
            "Architectural AST check",
            "python",
            "scripts/architecture_check.py",
        ),
        *_documentation_steps(),
        _step(
            "python-coverage",
            "Pytest and branch coverage",
            "pytest",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
        ),
    ]
    matrix = REPO / "docs/dev/plugin-decoupling/audit/removability_matrix.json"
    if not matrix.exists():
        return steps
    for script, step_id, name in (
        (
            "scripts/architecture/enforce_provider_boundaries.py",
            "provider-boundaries",
            "Provider architecture boundaries",
        ),
        (
            "scripts/architecture/enforce_provider_manifests.py",
            "provider-manifests",
            "Provider manifests and graph",
        ),
        (
            "scripts/architecture/enforce_provider_evidence.py",
            "provider-evidence",
            "Provider removability evidence",
        ),
    ):
        if (REPO / script).exists():
            steps.append(
                _step(
                    step_id,
                    name,
                    "python",
                    script,
                    "--root",
                    ".",
                    "--matrix",
                    matrix.relative_to(REPO).as_posix(),
                )
            )
    return steps


def _ui_steps() -> list[ValidationStep]:
    """Return comprehensive UI validation steps."""
    return [
        _step(
            "ui-typecheck",
            "UI typecheck",
            "npm",
            "run",
            "typecheck",
            working_directory=UI_ROOT,
            locked_python=False,
        ),
        _step(
            "ui-test",
            "UI Vitest suite",
            "npm",
            "run",
            "test",
            working_directory=UI_ROOT,
            locked_python=False,
        ),
        _step(
            "ui-build",
            "UI production build",
            "npm",
            "run",
            "build",
            working_directory=UI_ROOT,
            locked_python=False,
        ),
    ]


def _workflow_steps(*, include_static: bool) -> list[ValidationStep]:
    """Return workflow-controller validation steps."""
    steps = _quality_steps() if include_static else []
    if include_static:
        steps.append(_step("workflow-mypy", "Workflow mypy", "mypy", ".agents"))
    steps.extend(
        (
            _step(
                "workflow-tests",
                "Workflow controller tests",
                "pytest",
                "--no-cov",
                ".agents/tests",
            ),
            _step(
                "workflow-self-test",
                "Workflow controller self-test",
                "python",
                ".agents/orchestrator.py",
                "self-test",
            ),
        )
    )
    return steps


def _affected_python_steps(decision: RoutingDecision) -> list[ValidationStep]:
    """Return focused Python checks for a routed affected set."""
    existing_python = tuple(
        path
        for path in decision.changed_paths
        if path.endswith((".py", ".pyi")) and (REPO / path).is_file()
    )
    steps: list[ValidationStep] = []
    if existing_python:
        steps.extend(
            (
                _step(
                    "affected-ruff-format",
                    "Affected Ruff format check",
                    "ruff",
                    "format",
                    "--check",
                    *existing_python,
                ),
                _step(
                    "affected-ruff-lint",
                    "Affected Ruff lint check",
                    "ruff",
                    "check",
                    *existing_python,
                ),
            )
        )
        typed_paths = tuple(
            path for path in existing_python if path.startswith(("app/", ".agents/"))
        )
        if typed_paths:
            steps.append(_step("affected-mypy", "Affected mypy", "mypy", *typed_paths))
    steps.append(
        _step(
            "affected-pytest",
            "Affected Python tests",
            "pytest",
            "--no-cov",
            *decision.python_test_paths,
        )
    )
    return steps


def _affected_ui_steps(decision: RoutingDecision) -> list[ValidationStep]:
    """Return type and focused Vitest checks for affected UI scope."""
    return [
        _step(
            "ui-typecheck",
            "UI typecheck",
            "npm",
            "run",
            "typecheck",
            working_directory=UI_ROOT,
            locked_python=False,
        ),
        _step(
            "affected-ui-test",
            "Affected UI tests",
            "npm",
            "run",
            "test",
            "--",
            *decision.ui_test_paths,
            working_directory=UI_ROOT,
            locked_python=False,
        ),
    ]


def _family_steps(
    family: str,
    decision: RoutingDecision,
    *,
    comprehensive_python: bool,
) -> list[ValidationStep]:
    """Return steps for one internal validation family.

    Returns:
        Ordered steps for the family.

    Raises:
        RoutingError: If the router emits an unsupported family.
    """
    if family == "python":
        return _python_steps()
    if family == "python-affected":
        return _affected_python_steps(decision)
    if family == "ui":
        return _ui_steps()
    if family == "ui-affected":
        return _affected_ui_steps(decision)
    if family == "workflow":
        return _workflow_steps(include_static=not comprehensive_python)
    if family == "documentation":
        return _documentation_steps()
    message = f"Unsupported internal validation family: {family}"
    raise RoutingError(message)


def build_steps(decision: RoutingDecision) -> tuple[ValidationStep, ...]:
    """Build and deduplicate commands for a routing decision.

    Args:
        decision: Deterministic routing decision.

    Returns:
        Ordered validation steps with unique command identities.

    Raises:
        RoutingError: If the route has no supported executable checks.
    """
    steps: list[ValidationStep] = []
    comprehensive_python = "python" in decision.families
    for family in decision.families:
        steps.extend(
            _family_steps(
                family,
                decision,
                comprehensive_python=comprehensive_python,
            )
        )

    unique: list[ValidationStep] = []
    seen_commands: set[tuple[Path, tuple[str, ...]]] = set()
    for step in steps:
        identity = (step.working_directory.resolve(), step.command())
        if identity not in seen_commands:
            unique.append(step)
            seen_commands.add(identity)
    if not unique:
        raise RoutingError("Validation routing produced no executable checks.")
    return tuple(unique)


def run_command(step: ValidationStep) -> StepResult:
    """Execute one validation command and return measured evidence.

    Args:
        step: Validation step to execute.

    Returns:
        Measured command result.
    """
    command = step.command()
    print("========================================")
    print(f"Running {step.name}...")
    print(f"Working directory: {step.working_directory}")
    print(f"Command: {' '.join(command)}")
    print("========================================\n")
    started = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=step.working_directory,
        capture_output=False,
        check=False,
    )
    elapsed = time.perf_counter() - started
    status = "SUCCESS" if result.returncode == 0 else "FAILURE"
    print(f"\n[{status}] {step.name}: {elapsed:.2f}s (exit {result.returncode})\n")
    return StepResult(
        step_id=step.step_id,
        name=step.name,
        command=command,
        working_directory=str(step.working_directory),
        duration_seconds=round(elapsed, 6),
        exit_code=result.returncode,
    )


def _decision_payload(decision: RoutingDecision) -> dict[str, object]:
    """Serialize a routing decision without claiming validation trust.

    Returns:
        JSON-compatible routing payload.
    """
    return {
        "requested_profile": decision.requested_profile,
        "selected_families": list(decision.families),
        "changed_paths": list(decision.changed_paths),
        "python_test_paths": list(decision.python_test_paths),
        "ui_test_paths": list(decision.ui_test_paths),
        "reasons": list(decision.reasons),
        "widened_to_full": decision.widened_to_full,
        "candidate": asdict(decision.candidate),
    }


def _write_report(
    path: Path,
    *,
    decision: RoutingDecision,
    steps: Sequence[ValidationStep],
    results: Sequence[StepResult],
    explain_only: bool,
) -> None:
    """Write a deterministic diagnostic report for this invocation."""
    payload = {
        "schema_version": 1,
        "report_kind": "diagnostic-not-reusable-validation-receipt",
        "explain_only": explain_only,
        "decision": _decision_payload(decision),
        "steps": [
            {
                "step_id": step.step_id,
                "name": step.name,
                "command": list(step.command()),
                "working_directory": str(step.working_directory),
            }
            for step in steps
        ],
        "results": [asdict(result) for result in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _print_explanation(
    decision: RoutingDecision, steps: Sequence[ValidationStep]
) -> None:
    """Print candidate identity, routing reasons, and exact commands."""
    candidate = decision.candidate
    print(f"Requested profile: {decision.requested_profile}")
    print(f"Selected families: {', '.join(decision.families)}")
    print(f"Base: {candidate.base_commit or 'LOCAL/UNSPECIFIED'}")
    print(f"Head: {candidate.head_commit or 'WORKING_TREE/UNSPECIFIED'}")
    print(f"Merge base: {candidate.merge_base or 'UNSPECIFIED'}")
    print("Changed paths:")
    for path in decision.changed_paths:
        print(f"  - {path}")
    print("Routing reasons:")
    for reason in decision.reasons:
        print(f"  - {reason}")
    print("Commands:")
    for step in steps:
        print(f"  - [{step.working_directory}] {' '.join(step.command())}")


def _parser() -> argparse.ArgumentParser:
    """Build the validation command-line parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=PUBLIC_PROFILES,
        default="full",
        help="Validation profile; defaults conservatively to full.",
    )
    parser.add_argument("--base", help="Integration base Git revision.")
    parser.add_argument("--head", help="Candidate Git revision.")
    parser.add_argument(
        "--reviewed-worktree",
        action="store_true",
        help=(
            "Include the controller-frozen reviewed worktree in an integration "
            "candidate. Valid only with --profile integration, --base and --head."
        ),
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Print routing and commands without executing them.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Write a diagnostic JSON report (not a reusable receipt).",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Route and run the requested validation profile.

    Args:
        arguments: Optional arguments for tests; defaults to process arguments.

    Returns:
        Process-compatible exit code.
    """
    options = _parser().parse_args(arguments)
    try:
        decision = route_validation(
            REPO,
            profile=options.profile,
            base_ref=options.base,
            head_ref=options.head,
            reviewed_worktree=options.reviewed_worktree,
        )
        steps = build_steps(decision)
    except RoutingError as exc:
        print(f"[FAILURE] Validation routing failed: {exc}", file=sys.stderr)
        return 2

    if options.explain:
        _print_explanation(decision, steps)
        if options.report is not None:
            _write_report(
                options.report,
                decision=decision,
                steps=steps,
                results=(),
                explain_only=True,
            )
        return 0

    results: list[StepResult] = []
    for step in steps:
        result = run_command(step)
        results.append(result)
        if result.exit_code != 0:
            break
    if options.report is not None:
        _write_report(
            options.report,
            decision=decision,
            steps=steps,
            results=results,
            explain_only=False,
        )
    if results and results[-1].exit_code != 0:
        return results[-1].exit_code
    print("========================================")
    print("[SUCCESS] Selected quality gates passed!")
    print("========================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
