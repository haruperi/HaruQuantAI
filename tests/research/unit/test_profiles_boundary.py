"""Unit evidence for the lazily-resolved Research profiles package boundary."""

from __future__ import annotations

import ast
import inspect
import subprocess
import sys
from pathlib import Path

import app.services.research.profiles as profiles_pkg
import pytest

_BOUNDARY = Path(inspect.getfile(profiles_pkg))

# Sibling features `workflow.py` composes. Resolving a profile capability that
# does not need them must not load them.
_HEAVY_SIBLINGS = (
    "data",
    "features",
    "leakage",
    "market_structure",
    "metrics",
    "modeling",
    "seasonality",
    "statistics",
    "studies",
)


def _type_checking_import_names() -> set[str]:
    """Collect names imported inside the package's ``TYPE_CHECKING`` block.

    Returns:
        Names declared for type checkers only.
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


def test_every_declared_export_resolves() -> None:
    """Resolve the whole package surface so a broken export cannot reach runtime."""
    unresolved = [
        name
        for name in profiles_pkg._EXPORTS
        if not callable(getattr(profiles_pkg, name, None))
    ]
    assert not unresolved


def test_surface_declarations_agree() -> None:
    """`__all__`, the lazy table, and the type-checking imports must match."""
    exports = set(profiles_pkg._EXPORTS)
    assert set(profiles_pkg.__all__) == exports
    assert _type_checking_import_names() == exports
    assert list(profiles_pkg.__all__) == sorted(profiles_pkg.__all__)


def test_unknown_attribute_raises_attribute_error() -> None:
    """A name outside the package surface is rejected rather than resolved."""
    with pytest.raises(AttributeError, match="has no attribute"):
        profiles_pkg.definitely_not_a_profile_export  # noqa: B018


def test_rendering_does_not_load_the_edge_lab_pipeline() -> None:
    """Resolving the report renderer must not import the workflow's siblings.

    Runs in a subprocess because `sys.modules` is already populated inside the
    test session; module-loading isolation cannot be observed in-process. This
    is the one test here that exceeds the usual unit-test time budget, and the
    subprocess is the behaviour under test rather than incidental IO.
    """
    program = (
        "import sys\n"
        "from app.services.research import render_research_report\n"
        "assert callable(render_research_report)\n"
        "loaded = [n for n in "
        f"{_HEAVY_SIBLINGS!r}"
        " if f'app.services.research.{n}' in sys.modules]\n"
        "print(','.join(loaded))\n"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
