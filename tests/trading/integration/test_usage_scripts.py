"""Integration evidence that every documented Trading usage script is runnable."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_contracts.py",
    "02_state.py",
    "03_validation.py",
    "04_routing.py",
    "05_reconciliation.py",
    "06_monitoring.py",
    "07_live.py",
    "08_actions.py",
    "09_reporting.py",
    "10_protective_orders.py",
    "11_trade_ownership.py",
    "12_session_registry.py",
)

_README = Path(__file__).parents[3] / "app" / "services" / "trading" / "README.md"
_FEATURE_PATTERN = re.compile(
    r"^\|\s*Completed\s*\|\s*`FEAT-TRD-(\d{2})`", re.MULTILINE
)
_REQUIREMENT_PATTERN = re.compile(
    r"^\|\s*Completed\s*\|\s*`FR-TRD-(\d{3})`", re.MULTILINE
)
_EXAMPLE_PATTERN = re.compile(r"^def fr_trd_(\d{3})", re.MULTILINE)


def test_numbered_usage_registry_is_exact() -> None:
    """Require one numbered program per feature and exact active-FR parity."""
    usage_directory = Path(__file__).parents[1] / "usage" / "features"
    readme = _README.read_text(encoding="utf-8")
    feature_ids = set(_FEATURE_PATTERN.findall(readme))
    numbered = tuple(
        sorted(path.name for path in usage_directory.glob("[0-9][0-9]_*.py"))
    )
    assert feature_ids == {f"{index:02d}" for index in range(1, 13)}
    assert numbered == _USAGE_SCRIPTS
    assert not (usage_directory / "features.py").exists()

    active_requirements = set(_REQUIREMENT_PATTERN.findall(readme))
    examples: set[str] = set()
    for script_name in numbered:
        source = (usage_directory / script_name).read_text(encoding="utf-8")
        script_examples = set(_EXAMPLE_PATTERN.findall(source))
        assert examples.isdisjoint(script_examples), script_name
        examples.update(script_examples)
    assert "011" not in active_requirements
    assert examples == active_requirements


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_trading_usage_script_executes(script_name: str) -> None:
    """Run one standalone Trading usage script in an isolated Python process."""
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
    requirements = set(
        _EXAMPLE_PATTERN.findall(
            (usage_directory / script_name).read_text(encoding="utf-8")
        )
    )
    for requirement in requirements:
        assert f"SUCCESS: FR-TRD-{requirement}" in completed.stdout
    assert completed.stdout.count("Data ->") >= len(requirements)
