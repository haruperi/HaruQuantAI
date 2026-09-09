"""Tests for the public profile-driven validation entry point."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
from scripts.validation_router import CandidateChanges, RoutingDecision

from scripts import ci_check


def _decision(
    *families: str,
    requested: str = "full",
) -> RoutingDecision:
    """Build a bounded routing decision for runner tests."""
    return RoutingDecision(
        requested_profile=requested,
        families=families,
        changed_paths=("scripts/ci_check.py",),
        python_test_paths=(),
        ui_test_paths=(),
        reasons=("test decision",),
        widened_to_full=False,
        candidate=CandidateChanges(
            base_ref="main",
            head_ref="HEAD",
            base_commit="a" * 40,
            head_commit="b" * 40,
            merge_base="a" * 40,
            paths=("scripts/ci_check.py",),
            deleted_paths=(),
            renamed_paths=(),
            local_paths=(),
        ),
    )


def test_pytest_defaults_do_not_enable_coverage() -> None:
    """Normal pytest remains free of global coverage and HTML generation."""
    payload = tomllib.loads((ci_check.REPO / "pyproject.toml").read_text("utf-8"))
    addopts = payload["tool"]["pytest"]["ini_options"]["addopts"]

    assert not any(str(option).startswith("--cov") for option in addopts)
    assert payload["tool"]["coverage"]["run"]["branch"] is True
    assert payload["tool"]["coverage"]["report"]["fail_under"] == 80


def test_full_profile_contains_every_family_once() -> None:
    """Full validation includes Python, UI, and workflow without duplicates."""
    steps = ci_check.build_steps(_decision("python", "ui", "workflow"))
    commands = [step.command() for step in steps]
    ids = [step.step_id for step in steps]

    assert ids.count("ruff-format") == 1
    assert ids.count("ruff-lint") == 1
    assert "python-coverage" in ids
    assert "ui-typecheck" in ids
    assert "ui-test" in ids
    assert "ui-build" in ids
    assert "workflow-tests" in ids
    assert "workflow-self-test" in ids
    assert "workflow-mypy" not in ids
    assert len(commands) == len(set(commands))


def test_comprehensive_python_coverage_is_explicit_without_html() -> None:
    """The Python profile retains the floor without iterative HTML output."""
    steps = ci_check.build_steps(_decision("python", requested="python"))
    coverage = next(step for step in steps if step.step_id == "python-coverage")

    assert "--cov=app" in coverage.arguments
    assert "--cov-fail-under=80" in coverage.arguments
    assert "--cov-report=term-missing" in coverage.arguments
    assert "--cov-report=html" not in coverage.arguments


def test_python_commands_use_locked_environment() -> None:
    """Every Python runner step preserves the dependency lock."""
    steps = ci_check.build_steps(_decision("python", "workflow"))

    assert all(
        step.command()[:3] == ("uv", "run", "--locked")
        for step in steps
        if step.locked_python
    )


def test_no_argument_invocation_remains_conservative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public no-argument interface selects full validation."""
    seen: dict[str, object] = {}
    decision = _decision("python", "ui", "workflow")

    def route(*_args: object, **kwargs: object) -> RoutingDecision:
        seen["profile"] = kwargs["profile"]
        return decision

    monkeypatch.setattr(ci_check, "route_validation", route)
    monkeypatch.setattr(ci_check, "build_steps", lambda _decision: ())

    assert ci_check.main([]) == 0
    assert seen["profile"] == "full"


def test_explain_lists_commands_without_execution(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Explain mode is read-only and exposes exact routing decisions."""
    decision = _decision("documentation", requested="affected")
    monkeypatch.setattr(ci_check, "route_validation", lambda *_a, **_kw: decision)
    monkeypatch.setattr(
        ci_check,
        "run_command",
        lambda _step: pytest.fail("explain mode executed a command"),
    )

    assert ci_check.main(["--profile", "affected", "--explain"]) == 0
    output = capsys.readouterr().out
    assert "Selected families: documentation" in output
    assert "validate_feature_docs.py" in output


def test_report_records_candidate_commands_and_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Diagnostic JSON binds routing and observations without claiming receipt trust."""
    decision = _decision("documentation", requested="affected")
    monkeypatch.setattr(ci_check, "route_validation", lambda *_a, **_kw: decision)
    monkeypatch.setattr(
        ci_check,
        "run_command",
        lambda step: ci_check.StepResult(
            step_id=step.step_id,
            name=step.name,
            command=step.command(),
            working_directory=str(step.working_directory),
            duration_seconds=0.25,
            exit_code=0,
        ),
    )
    report = tmp_path / "report.json"

    assert ci_check.main(["--profile", "affected", "--report", str(report)]) == 0
    payload = json.loads(report.read_text("utf-8"))
    assert payload["report_kind"] == "diagnostic-not-reusable-validation-receipt"
    assert payload["decision"]["candidate"]["head_commit"] == "b" * 40
    assert payload["results"][0]["exit_code"] == 0


def test_execution_stops_at_first_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed prerequisite prevents later steps from running."""
    decision = _decision("ui", requested="ui")
    monkeypatch.setattr(ci_check, "route_validation", lambda *_a, **_kw: decision)
    executed: list[str] = []

    def run(step: ci_check.ValidationStep) -> ci_check.StepResult:
        executed.append(step.step_id)
        exit_code = 9 if len(executed) == 1 else 0
        return ci_check.StepResult(
            step_id=step.step_id,
            name=step.name,
            command=step.command(),
            working_directory=str(step.working_directory),
            duration_seconds=0.1,
            exit_code=exit_code,
        )

    monkeypatch.setattr(ci_check, "run_command", run)

    assert ci_check.main(["--profile", "ui"]) == 9
    assert executed == ["ui-typecheck"]


def test_routing_failure_returns_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid candidate input cannot be represented as successful validation."""
    monkeypatch.setattr(
        ci_check,
        "route_validation",
        lambda *_a, **_kw: (_ for _ in ()).throw(ci_check.RoutingError("invalid")),
    )

    assert ci_check.main(["--profile", "integration"]) == 2
