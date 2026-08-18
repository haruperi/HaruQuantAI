"""Integration evidence that every documented Analytics usage script is runnable."""

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_contracts.py",
    "02_adapters.py",
    "03_metrics.py",
    "04_reports.py",
    "05_dashboards.py",
    "06_scoring.py",
    "07_journal.py",
    "08_behavior.py",
    "09_emergency_response.py",
    "10_qualification.py",
    "11_workbench.py",
)

_README_REQUIREMENTS = {
    int(match.group(1))
    for match in re.finditer(
        r"^\| Completed \| `FR-ANLT-(\d{3})` \|",
        (Path(__file__).parents[3] / "app/services/analytics/README.md").read_text(
            encoding="utf-8"
        ),
        re.MULTILINE,
    )
}


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_analytics_usage_script_executes(script_name: str) -> None:
    """Run one standalone Analytics usage script in an isolated Python process."""
    usage_directory = Path(__file__).parents[1] / "usage" / "features"
    completed = subprocess.run(  # noqa: S603 - fixed repository-controlled command
        [sys.executable, str(usage_directory / script_name)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        timeout=120,
    )
    assert completed.returncode == 0, (
        f"{script_name} failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert completed.stdout.strip(), f"{script_name} produced no visible output"
    assert "SUCCESS:" in completed.stdout
    assert "Data ->" in completed.stdout


def test_numbered_programs_cover_every_completed_requirement_once() -> None:
    """Require exact Completed-FR ownership and package-root-only usage imports."""
    usage_directory = Path(__file__).parents[1] / "usage" / "features"
    assert {path.name for path in usage_directory.glob("*.py")} == {
        *_USAGE_SCRIPTS,
        "conftest.py",
    }
    owners: dict[int, str] = {}
    for script_name in _USAGE_SCRIPTS:
        path = usage_directory / script_name
        source = path.read_text(encoding="utf-8")
        module = ast.parse(source)
        functions = {
            node.name: node
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        main = functions["main"]
        called = {
            node.func.id
            for node in ast.walk(main)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        for name, function in functions.items():
            match = re.fullmatch(r"fr_anlt_(\d{3})", name)
            if match is None:
                continue
            requirement = int(match.group(1))
            assert requirement not in owners
            owners[requirement] = script_name
            assert name in called
            function_source = ast.get_source_segment(source, function) or ""
            assert (
                "Data ->" in function_source or "_contract_evidence" in function_source
            )
            assert (
                "_format_result" in function_source
                or "_contract_evidence" in function_source
            )
        assert not any(
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("app.services.analytics.")
            for node in ast.walk(module)
        )
    assert set(owners) == _README_REQUIREMENTS
