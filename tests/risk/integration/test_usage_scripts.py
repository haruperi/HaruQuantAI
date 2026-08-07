"""Integration evidence that every documented Risk usage script is runnable."""

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_contracts.py",
    "02_config.py",
    "03_portfolio.py",
    "04_sizing.py",
    "05_audit.py",
    "06_limits.py",
    "07_regimes.py",
    "08_admission.py",
    "09_allocation.py",
    "10_approvals.py",
    "11_validity.py",
    "12_governor.py",
    "13_kill_switch.py",
    "14_scenarios.py",
    "15_reporting.py",
    "features.py",
)


def _normalized(value: str) -> str:
    """Remove presentation whitespace for exact specification comparison."""
    return "".join(value.split())


def _documented_usage_requirements() -> dict[str, dict[str, str]]:
    """Return each Section 4 requirement assigned to its feature usage file."""
    repository = Path(__file__).parents[3]
    readme = (repository / "app" / "services" / "risk" / "README.md").read_text(
        encoding="utf-8"
    )
    section_four = readme.split("## 4.", maxsplit=1)[1].split("## 5.", maxsplit=1)[0]
    feature_number: int | None = None
    expected = {name: {} for name in _USAGE_SCRIPTS if name != "features.py"}
    for line in section_four.splitlines():
        heading = re.match(r"### 4\.(\d+) ", line)
        if heading is not None:
            feature_number = int(heading.group(1))
            continue
        if not line.startswith("|") or "FR-RISK-" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        requirement = re.search(r"FR-RISK-\d{3}", cells[1])
        if requirement is not None and feature_number is not None:
            expected[_USAGE_SCRIPTS[feature_number - 1]][requirement.group()] = cells[2]
    return expected


def test_usage_functions_reconcile_exactly_with_section_four() -> None:
    """Require one exact, documented, main-reachable function per Risk FR."""
    usage_directory = Path(__file__).parents[1] / "usage" / "features"
    documented = _documented_usage_requirements()
    observed: set[str] = set()
    for script_name, requirements in documented.items():
        tree = ast.parse(
            (usage_directory / script_name).read_text(encoding="utf-8"),
            filename=script_name,
        )
        functions = {
            node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        main_names = {
            node.id
            for node in ast.walk(functions["main"])
            if isinstance(node, ast.Name)
        }
        for requirement_id, responsibility in requirements.items():
            function_name = requirement_id.lower().replace("-", "_")
            function = functions.get(function_name)
            assert function is not None, f"{script_name} missing {function_name}"
            docstring = ast.get_docstring(function, clean=True) or ""
            assert requirement_id in docstring
            assert _normalized(responsibility) in _normalized(docstring)
            assert function_name in main_names
            observed.add(requirement_id)
        unexpected = {
            name.upper().replace("_", "-")
            for name in functions
            if name.startswith("fr_risk_")
        } - set(requirements)
        assert unexpected == set()
    assert len(observed) == sum(len(items) for items in documented.values())


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_risk_usage_script_executes(script_name: str) -> None:
    """Run one standalone Risk usage script in an isolated Python process and enforce output contracts."""
    usage_directory = Path(__file__).parents[1] / "usage" / "features"
    completed = subprocess.run(  # noqa: S603
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
    stdout = completed.stdout
    assert stdout.strip(), f"{script_name} produced no visible output"

    documented = _documented_usage_requirements()
    if script_name in documented:
        requirements = documented[script_name]
        for req_id in requirements:
            # 1. Assert exactly one SUCCESS: FR-RISK-NNN line
            success_matches = re.findall(
                rf"^SUCCESS:\s+{req_id}$", stdout, re.MULTILINE
            )
            assert len(success_matches) == 1, (
                f"{script_name} must output exactly one SUCCESS: {req_id} line, got {len(success_matches)}"
            )

        # 2. Assert stdout contains at least one Data -> line
        data_matches = re.findall(r"^Data\s+->", stdout, re.MULTILINE)
        assert len(data_matches) >= len(requirements), (
            f"{script_name} must output at least {len(requirements)} Data -> lines, got {len(data_matches)}"
        )

    # 3. Assert zero secret-like key/value patterns in stdout
    secret_patterns = (
        r"password\s*=",
        r"signing_key\s*=",
        r"private_key\s*=",
        r"secret_key\s*=",
    )
    for pattern in secret_patterns:
        match = re.search(pattern, stdout, re.IGNORECASE)
        assert match is None, (
            f"{script_name} stdout contains potential secret key/value pattern: {pattern}"
        )
