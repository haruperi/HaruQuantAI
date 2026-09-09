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
    python_test_paths: tuple[str, ...] = (),
    ui_test_paths: tuple[str, ...] = (),
) -> RoutingDecision:
    """Build a bounded routing decision for runner tests."""
    return RoutingDecision(
        requested_profile=requested,
        families=families,
        changed_paths=("scripts/ci_check.py",),
        python_test_paths=python_test_paths,
        ui_test_paths=ui_test_paths,
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


def test_affected_python_is_path_bounded_without_coverage() -> None:
    """The Python editing/push path runs selected tests without coverage."""
    selected = "tests/services/workspace/manage_artifacts"
    steps = ci_check.build_steps(
        _decision(
            "python-affected",
            requested="affected",
            python_test_paths=(selected,),
        )
    )
    ids = [step.step_id for step in steps]
    pytest_step = next(step for step in steps if step.step_id == "affected-pytest")

    assert "python-coverage" not in ids
    assert pytest_step.arguments == ("pytest", "--no-cov", selected)


def test_affected_ui_is_path_bounded_without_production_build() -> None:
    """The UI editing/push path runs selected tests but not a full build."""
    selected = "src/widgets/workspaces/store.test.ts"
    steps = ci_check.build_steps(
        _decision(
            "ui-affected",
            requested="affected",
            ui_test_paths=(selected,),
        )
    )
    ids = [step.step_id for step in steps]
    test_step = next(step for step in steps if step.step_id == "affected-ui-test")

    assert ids == ["ui-typecheck", "affected-ui-test"]
    assert "ui-build" not in ids
    assert test_step.arguments[-1] == selected


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


def test_runner_writes_hash_bound_full_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Controller mode stores complete command output outside the report."""
    step = ci_check._step(
        "log-test",
        "Log test",
        "python",
        "-c",
        "print('complete output')",
    )

    result = ci_check.run_command(step, log_dir=tmp_path)

    assert result.exit_code == 0
    assert result.log_path is not None
    assert (
        Path(result.log_path).read_text(encoding="utf-8").startswith("complete output")
    )
    assert result.log_sha256 is not None


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


def test_reviewed_worktree_flag_is_forwarded_to_router(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The controller-only candidate mode reaches deterministic routing."""
    seen: dict[str, object] = {}
    decision = _decision("ui", requested="integration")

    def route(*_args: object, **kwargs: object) -> RoutingDecision:
        seen.update(kwargs)
        return decision

    monkeypatch.setattr(ci_check, "route_validation", route)
    monkeypatch.setattr(ci_check, "build_steps", lambda _decision: ())

    assert (
        ci_check.main(
            [
                "--profile",
                "integration",
                "--base",
                "main",
                "--head",
                "HEAD",
                "--reviewed-worktree",
            ]
        )
        == 0
    )
    assert seen["reviewed_worktree"] is True


def test_pre_push_uses_affected_validation_without_inline_coverage() -> None:
    """Routine pushes no longer embed the former broad validation commands."""
    config = (ci_check.REPO / ".pre-commit-config.yaml").read_text("utf-8")
    pre_commit = config[: config.index("- id: affected-validation")]
    pre_push = config[config.index("- id: affected-validation") :]

    assert "pytest" not in pre_commit
    assert "mypy" not in pre_commit
    assert "npm run build" not in pre_commit
    assert "--profile affected --base origin/main --head HEAD" in pre_push
    assert "--cov=app" not in pre_push
    assert "--cov-report=html" not in pre_push
    assert "- id: workflow-tests" not in pre_push
    assert "- id: workflow-self-test" not in pre_push
    assert "\\.github/workflows/" in pre_push
    assert "\\.pre-commit-config\\.yaml$" in pre_push


def test_ci_defines_locked_stable_acceptance_status() -> None:
    """Remote qualification exposes one stable lock-preserving job name."""
    workflow = (ci_check.REPO / ".github/workflows/ci.yml").read_text("utf-8")

    assert "  acceptance:\n" in workflow
    assert "    name: acceptance\n" in workflow
    assert "fetch-depth: 0" in workflow
    assert "uv sync --locked --all-extras --dev" in workflow
    assert "working-directory: app/ui\n        run: npm ci" in workflow
    assert "--profile integration" in workflow
    assert "--profile full" in workflow
    assert "test_config_disable_matrix.py" not in workflow
