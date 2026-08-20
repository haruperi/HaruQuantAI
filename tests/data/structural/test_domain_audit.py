"""Mechanical conformance guards for the fourteen-feature Data domain."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from app.services import data

_DATA_ROOT = Path("app/services/data")
_USAGE_ROOT = Path("tests/data/usage/features")
_EXCLUDED_DIRECTORIES = {
    "__pycache__",
    "_shared",
    "contracts",
    "migrations",
    "persistence",
    "schemas",
}


def _registry_rows() -> tuple[tuple[str, str], ...]:
    """Return current feature identifiers and owning folders from the registry.

    Returns:
        Ordered pairs of feature identifier and module-folder name.

    Raises:
        AssertionError: If the canonical registry section cannot be located.
    """
    readme = (_DATA_ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(
        r"^### Feature Registry\s*$([\s\S]*?)(?=^####?\s)",
        readme,
        flags=re.MULTILINE,
    )
    assert match is not None
    return tuple(
        (feature_id, module.rstrip("/"))
        for feature_id, module in re.findall(
            r"\| Completed \| `?(FEAT-DATA-\d{2})`?[^|]*\| `?([a-z_]+/)`? \|",
            match.group(1),
        )
    )


def test_registry_folders_and_usage_programs_reconcile() -> None:
    """Require one current registry row, folder, and usage program per feature."""
    rows = _registry_rows()
    assert rows == tuple(
        (f"FEAT-DATA-{index:02d}", module)
        for index, module in enumerate(
            (
                "market_data",
                "datasets",
                "synthetic_data",
                "transformation",
                "alignment",
                "integrity",
                "time_sessions",
                "economic_calendar",
                "sources",
                "market_events",
                "data_jobs",
                "evidence",
                "runtime_stores",
                "replay",
                "sqx_source",
            ),
            start=1,
        )
    )
    production_folders = {
        path.name
        for path in _DATA_ROOT.iterdir()
        if path.is_dir()
        and any(path.glob("*.py"))
        and path.name not in _EXCLUDED_DIRECTORIES
        and not path.name.startswith(".")
    }
    assert production_folders == {module for _, module in rows}
    assert {path.stem for path in _USAGE_ROOT.glob("[0-9][0-9]_*.py")} == {
        f"{index:02d}_{module}" for index, (_, module) in enumerate(rows, start=1)
    }


def test_package_root_and_public_surface_are_conforming() -> None:
    """Require the approved root files and a function-only literal public API."""
    root_python_files = {path.name for path in _DATA_ROOT.glob("*.py")}
    assert root_python_files == {"__init__.py", "_limits.py", "_settings.py"}
    tree = ast.parse((_DATA_ROOT / "__init__.py").read_text(encoding="utf-8"))
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        )
    )
    literal_exports = ast.literal_eval(assignment.value)
    assert tuple(literal_exports) == tuple(data.__all__)
    assert all(callable(getattr(data, name)) for name in data.__all__)
    assert all(not isinstance(getattr(data, name), type) for name in data.__all__)


def test_readme_usage_evidence_paths_exist() -> None:
    """Require every current README usage-program reference to resolve."""
    readme = (_DATA_ROOT / "README.md").read_text(encoding="utf-8")
    referenced_paths = set(re.findall(r"tests/data/usage/[A-Za-z0-9_./-]+\.py", readme))
    missing = sorted(path for path in referenced_paths if not Path(path).is_file())
    assert not missing, f"Missing Data usage evidence paths: {missing}"
