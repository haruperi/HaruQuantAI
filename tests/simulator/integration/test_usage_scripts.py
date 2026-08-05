"""Integration evidence that every documented Simulator usage script is runnable."""

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_validation.py",
    "02_state.py",
    "03_timeline.py",
    "04_accounting.py",
    "05_execution.py",
    "06_journal.py",
    "07_run.py",
    "08_errors.py",
    "09_reporting.py",
    "features.py",
)

_USAGE_REQUIREMENTS = {
    "01_validation.py": {1, 2, 3},
    "02_state.py": {41, 97, 98, 99, 100, 101, 102},
    "03_timeline.py": {4, 5, 6},
    "04_accounting.py": {7, 8, 9, 10, 11, 12, 39, 42},
    "05_execution.py": {18, 19, 20, 21, 22, 23, 38, 43},
    "06_journal.py": {13, 14, 15, 16, 17},
    "07_run.py": {29, 30, 31, 32, 34},
    "08_errors.py": {35, 36, 37},
    "09_reporting.py": {24, 25, 26, 27, 28, 33, 40},
    "features.py": set(),
}

_README_REQUIREMENTS = {
    int(match.group(1)): match.group(2).strip()
    for match in re.finditer(
        r"^\| Completed \| `FR-SIM-(\d{3})` \| (.*?) \|",
        (Path(__file__).parents[3] / "app/services/simulator/README.md").read_text(
            encoding="utf-8"
        ),
        re.MULTILINE,
    )
}


def _normalized_text(value: str) -> str:
    """Collapse formatting whitespace for exact responsibility comparisons."""
    return " ".join(value.split())


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_simulator_usage_script_executes(script_name: str) -> None:
    """Run one standalone Simulator usage script in an isolated Python process."""
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


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_usage_script_maps_requirements_and_uses_root_api(script_name: str) -> None:
    """Require one callable demonstration per mapped FR and no deep public import."""
    usage_path = Path(__file__).parents[1] / "usage" / "features" / script_name
    module = ast.parse(usage_path.read_text(encoding="utf-8"))
    if script_name == "features.py":
        assert not any(
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("app.services.simulator.")
            for node in ast.walk(module)
        )
        return
    functions = {
        node.name: node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    main = functions["main"]
    called_from_main = {
        node.func.id
        for node in ast.walk(main)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    expected_functions = {
        f"fr_sim_{requirement:03d}" for requirement in _USAGE_REQUIREMENTS[script_name]
    }
    assert expected_functions <= functions.keys()
    assert expected_functions <= called_from_main
    for function_name in expected_functions:
        docstring = ast.get_docstring(functions[function_name]) or ""
        requirement = function_name.removeprefix("fr_sim_")
        assert f"FR-SIM-{requirement}" in docstring
        responsibility = _README_REQUIREMENTS[int(requirement)]
        assert _normalized_text(responsibility) in _normalized_text(docstring)
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.startswith("app.services.simulator.")
        for node in ast.walk(module)
    )
