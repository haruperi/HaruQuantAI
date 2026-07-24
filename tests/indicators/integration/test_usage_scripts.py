"""Integration evidence that every indicators usage script is runnable."""

import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_core.py",
    "02_candles.py",
    "03_trend.py",
    "04_momentum.py",
    "05_volatility.py",
    "06_volume.py",
)


# Exit code a usage script returns when the live market-data source is
# unavailable, signalling a skip rather than a real failure.
_LIVE_DATA_UNAVAILABLE_EXIT = 3
_REQUIREMENT_ROW = re.compile(
    r"^\| Completed \| `(?P<requirement>FR-INDI-\d{3})` "
    r"\| (?P<responsibility>.*?) \|",
    re.MULTILINE,
)


def test_usage_scripts_cover_exact_requirements_through_root_api() -> None:
    """Every FR has one exact, invoked package-root usage demonstration."""
    repository_root = Path(__file__).parents[3]
    usage_directory = Path(__file__).parents[1] / "usage"
    readme = (
        repository_root / "app" / "services" / "indicators" / "README.md"
    ).read_text(encoding="utf-8")
    responsibilities = {
        match.group("requirement"): match.group("responsibility")
        for match in _REQUIREMENT_ROW.finditer(readme)
    }
    discovered: dict[str, tuple[Path, ast.FunctionDef]] = {}

    for script_name in _USAGE_SCRIPTS:
        script_path = usage_directory / script_name
        tree = ast.parse(script_path.read_text(encoding="utf-8"))
        imports = [
            node.module
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("app.services.")
        ]
        assert set(imports) <= {"app.services.data", "app.services.indicators"}

        main_node = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        invoked_names = {
            node.id for node in ast.walk(main_node) if isinstance(node, ast.Name)
        }
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or not re.fullmatch(
                r"fr_indi_\d{3}", node.name
            ):
                continue
            requirement = node.name.replace("fr_indi_", "FR-INDI-")
            assert requirement not in discovered
            assert requirement in responsibilities
            assert responsibilities[requirement] in (ast.get_docstring(node) or "")
            assert node.name in invoked_names
            discovered[requirement] = (script_path, node)

    assert set(discovered) == set(responsibilities)


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_indicators_usage_script_executes_successfully(script_name: str) -> None:
    """Run one standalone usage script in an isolated Python process.

    A return code of ``0`` means the example ran fully against real data. A
    return code of ``3`` means the live market-data source was unavailable, so
    the example is skipped rather than failed (this keeps missing-data
    environments from masking a genuine regression). Data-owned persistence and
    logs are redirected to one disposable directory. Any other code fails.
    """
    usage_directory = Path(__file__).parents[1] / "usage"
    with tempfile.TemporaryDirectory(
        prefix="haruquant-indicators-usage-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        log_directory = temporary_root / "logs"
        log_directory.mkdir()
        environment = os.environ.copy()
        environment.update(
            {
                "DATABASE_URL": "sqlite:///usage.db",
                "DATA_DIR": str(temporary_root),
                "ENVIRONMENT": "dev",
                "LOG_DIRECTORY": str(log_directory),
                "LOG_FILE_PATH": str(log_directory / "app.log"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "RUNTIME_PROFILE": "research",
            }
        )
        completed = subprocess.run(  # noqa: S603 - fixed repository-controlled command
            [sys.executable, str(usage_directory / script_name)],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parents[3],
            env=environment,
            timeout=120,
        )
    if completed.returncode == _LIVE_DATA_UNAVAILABLE_EXIT:
        pytest.skip(f"{script_name}: live market data unavailable")
    assert not temporary_root.exists()
    assert completed.returncode == 0, (
        f"{script_name} failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
