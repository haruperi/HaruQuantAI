"""Unit evidence for the lazily-resolved Research public boundary."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import app.services.research as research_root
import pytest

_BOUNDARY = Path(inspect.getfile(research_root))


def _type_checking_import_names() -> set[str]:
    """Collect names imported inside the boundary's ``TYPE_CHECKING`` block.

    Returns:
        Public names declared for type checkers only.
    """
    tree = ast.parse(_BOUNDARY.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        guarded = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
            isinstance(test, ast.Attribute)
            and test.attr == "TYPE_CHECKING"
            and isinstance(test.value, ast.Name)
            and test.value.id == "typing"
        )
        if not guarded:
            continue
        for statement in node.body:
            if isinstance(statement, ast.ImportFrom):
                names.update(alias.asname or alias.name for alias in statement.names)
    return names


def _module_level_function_names() -> set[str]:
    """Collect public functions defined directly in the boundary module.

    Returns:
        Names of public module-level functions.
    """
    tree = ast.parse(_BOUNDARY.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }


def test_every_declared_export_resolves() -> None:
    """Resolve the whole boundary so a broken export cannot reach runtime.

    Lazy resolution defers import failures to first access; this test restores
    the fail-fast guarantee that eager imports provided.
    """
    unresolved: list[str] = []
    for name in research_root._EXPORTS:
        try:
            resolved = getattr(research_root, name)
        except (AttributeError, ImportError) as error:
            unresolved.append(f"{name}: {error}")
            continue
        if not callable(resolved):
            unresolved.append(f"{name}: not callable")
    assert not unresolved


def test_public_surface_declarations_agree() -> None:
    """`__all__`, the lazy table, and the type-checking imports must match."""
    exports = set(research_root._EXPORTS)
    functions = _module_level_function_names()
    assert set(research_root.__all__) == exports | functions
    assert _type_checking_import_names() == exports


def test_all_is_sorted_and_unique() -> None:
    """The declared public surface stays deterministic."""
    names = research_root.__all__
    assert len(set(names)) == len(names)
    assert list(names) == sorted(names)


def test_dir_lists_the_lazy_export_surface() -> None:
    """`dir()` reports the resolvable boundary names."""
    assert dir(research_root) == sorted(research_root._EXPORTS)


def test_unknown_attribute_raises_attribute_error() -> None:
    """A name outside the boundary is rejected rather than resolved."""
    with pytest.raises(AttributeError, match="has no attribute"):
        research_root.definitely_not_a_research_export  # noqa: B018


def test_function_only_public_api_surface() -> None:
    """Every public export is a standalone function, not a class or constant."""
    for name in research_root.__all__:
        assert inspect.isfunction(getattr(research_root, name)), name
