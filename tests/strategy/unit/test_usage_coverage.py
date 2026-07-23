"""Structural guarantees for the standalone Strategy usage programs."""

import ast
from pathlib import Path

from app.services import strategy
from app.utils import logger

_USAGE_DIR = Path(__file__).parents[1] / "usage"


def _programs() -> tuple[Path, ...]:
    """Return every numbered standalone usage program.

    Returns:
        Ordered numbered usage program paths.
    """
    logger.debug("Collecting standalone Strategy usage programs")
    return tuple(sorted(_USAGE_DIR.glob("[0-9]*_*.py")))


def test_every_public_symbol_has_usage_evidence() -> None:
    """Verify every exported symbol is called or constructed in a program."""
    logger.debug("Testing Strategy usage symbol coverage")
    referenced: set[str] = set()
    for path in _programs():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                referenced.add(node.id)
            elif isinstance(node, ast.Attribute):
                referenced.add(node.attr)
    missing = sorted(set(strategy.__all__) - referenced)
    assert not missing, f"public symbols without usage evidence: {missing}"


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
    features = tuple(
        path.name
        for path in sorted(
            (Path(__file__).parents[3] / "app/services/strategy").iterdir()
        )
        if path.is_dir() and (path / "__init__.py").exists()
    )
    assert len(_programs()) == len(features), sorted(features)
