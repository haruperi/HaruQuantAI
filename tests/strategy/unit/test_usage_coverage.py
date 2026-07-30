"""Structural guarantees for the standalone Strategy usage programs."""

import ast
from pathlib import Path

from app.services import strategy
from app.utils import get_logger

logger = get_logger(__name__)

_USAGE_DIR = Path(__file__).parents[1] / "usage"
_FEATURE_REQUIREMENTS = {
    "contracts": (
        "01_contracts.py",
        {
            *range(1, 18),
            35,
            38,
            39,
        },
    ),
    "diagnostics": ("02_diagnostics.py", {18, 19, 34}),
    "registry": ("03_registry.py", set(range(20, 25))),
    "intents": ("04_intents.py", {25, 26}),
    "replay": ("05_replay.py", {27, 29}),
    "checkpoints": ("06_checkpoints.py", {28, 30, 31}),
    "vectorized": ("07_vectorized.py", {32, 36}),
    "event": ("08_event.py", {33, 37}),
    "signals": ("09_signals.py", {47, 48}),
    "evaluators": ("10_strategy_library.py", set(range(40, 47))),
    "proposal_intake": ("11_proposal_intake.py", set(range(49, 54))),
}


def _programs() -> tuple[Path, ...]:
    """Return every numbered standalone usage program.

    Returns:
        Ordered numbered usage program paths.
    """
    logger.debug("Collecting standalone Strategy usage programs")
    return tuple(
        sorted(_USAGE_DIR.glob("[0-9]*_*.py"))
        + sorted((_USAGE_DIR / "workflows").glob("wf_*.py"))
    )


def test_every_public_symbol_is_called_in_usage_evidence() -> None:
    """Verify every exported symbol is actually called in a usage program."""
    logger.debug("Testing Strategy usage symbol coverage")
    referenced: set[str] = set()
    for path in _programs():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                referenced.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                referenced.add(node.func.attr)
    missing = sorted(set(strategy.__all__) - referenced)
    assert not missing, f"public symbols without usage evidence: {missing}"


def test_every_requirement_has_one_feature_local_demonstration() -> None:
    """Verify exact feature ownership for every FR demonstration function."""
    logger.debug("Testing Strategy requirement-to-usage mapping")
    observed: set[int] = set()
    for feature, (program_name, expected) in _FEATURE_REQUIREMENTS.items():
        tree = ast.parse((_USAGE_DIR / program_name).read_text(encoding="utf-8"))
        actual = {
            int(node.name.removeprefix("fr_str_"))
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("fr_str_")
        }
        assert actual == expected, feature
        duplicates = observed & actual
        assert not duplicates, f"duplicate FR demonstrations: {duplicates}"
        observed.update(actual)
    assert observed == set(range(1, 54))


def test_usage_programs_import_domain_dependencies_from_package_roots() -> None:
    """Verify usage programs contain no external deep service imports."""
    logger.debug("Testing Strategy usage import boundaries")
    for path in _programs():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            if node.module.startswith("app.services.strategy."):
                raise AssertionError(f"{path.name}: Strategy deep import {node.module}")
            service_parts = node.module.split(".")
            if service_parts[:2] == ["app", "services"] and len(service_parts) > 3:
                raise AssertionError(f"{path.name}: service deep import {node.module}")


def test_every_program_is_a_standalone_main_program() -> None:
    """Verify each program defines main() behind a __main__ guard."""
    logger.debug("Testing Strategy usage program structure")
    for path in _programs():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions = {
            node.name for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        assert "main" in functions, f"{path.name} defines no main()"
        guards = [
            node
            for node in tree.body
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
        ]
        assert guards, f"{path.name} has no __main__ guard"


def test_program_count_matches_feature_count() -> None:
    """Verify the domain keeps one usage program per registered feature."""
    logger.debug("Testing Strategy usage program cardinality")
    feature_directories = {
        path.name
        for path in (Path(__file__).parents[3] / "app/services/strategy").iterdir()
        if path.is_dir()
        and (path / "__init__.py").exists()
        and path.name != "migrations"
    }
    assert feature_directories == set(_FEATURE_REQUIREMENTS)
    assert {path.name for path in _USAGE_DIR.glob("[0-9]*_*.py")} == {
        program_name for program_name, _ in _FEATURE_REQUIREMENTS.values()
    }
