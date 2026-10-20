"""Enforce architectural invariants and PYTHON_MODULE.md Rules 0.1-0.8 across app/.

Description:
    Provides static AST and physical line-count qualification across `app/` to
    prevent architectural drift, circular or upward layer imports, SQLite
    persistence leakage, docstring bloat, and unapproved file growth. Invoked
    by `scripts/ci_check.py` and the `pre-commit` architecture gate hook.

Purpose:
    FEAT-ARCH-GATE: Enforce constitutional module and dependency boundaries.

Key Capabilities:
    - FR-ARCH-DOCSTRING-CEILING: Enforce <= 100 line top-of-file docstrings
      [`check_docstring_line_ceiling()`] (`INFO`).
    - FR-ARCH-FILE-SIZE-RATCHET: Enforce <= 1,000 physical lines with ratchet
      allowlist [`check_file_size_ceiling()`] (`INFO`).
    - FR-ARCH-FACADE-SIZE: Enforce <= 100 physical lines and no lazy `__getattr__`
      on `include/__init__.py` [`check_include_facade()`] (`INFO`).
    - FR-ARCH-PERSISTENCE-ISOLATION: Restrict `sqlite3` and DB helpers to
      `persistence.py` [`check_persistence_isolation()`] (`INFO`).
    - FR-ARCH-LAYERING-DAG: Enforce one-way import boundaries across `include`,
      `services`, and `host` [`check_one_way_layering_dag()`] (`INFO`).

Python API Usage:
    ```python
    import logging
    from scripts.check_architecture import main

    logging.basicConfig(level=logging.INFO)
    exit_code = main()
    ```

CLI Usage:
    ```bash
    uv run python scripts/check_architecture.py
    ```
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = REPO_ROOT / "app"

DOCSTRING_EXEMPT_NAMES = frozenset({"__init__.py", "_common.py", "_schema.py"})
DOCSTRING_RATCHET_ALLOWLIST: dict[str, int] = {}
FILE_SIZE_EXEMPT_PATHS = frozenset({"app/host/_schema.py"})

# Ratchet allowlist for pre-existing >1,000-line files scheduled for future slices.
RATCHET_ALLOWLIST: dict[str, int] = {
    "app/services/brokers/simulator.py": 1660,
    "app/services/brokers/ctrader.py": 1260,
}


def _iter_app_python_files() -> list[tuple[str, Path]]:
    """Return sorted `(rel_posix_path, path)` pairs for all Python files in `app/`."""
    return [
        (path.relative_to(REPO_ROOT).as_posix(), path)
        for path in sorted(APP_ROOT.rglob("*.py"))
    ]


def _extract_imports(tree: ast.Module, rel_path: str) -> list[str]:
    """Extract normalized absolute module import targets from an AST module."""
    pkg_parts = rel_path.removesuffix(".py").split("/")
    if pkg_parts[-1] != "__init__":
        pkg_parts = pkg_parts[:-1]
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level > 0:
                anchor = pkg_parts[: len(pkg_parts) - (node.level - 1)]
                prefix = ".".join(anchor)
                resolved = f"{prefix}.{base}" if base else prefix
            else:
                resolved = base
            if resolved:
                imports.append(resolved)
    return imports


def check_docstring_line_ceiling() -> list[str]:
    """Check <= 100 lines for top-of-file module docstrings across `app/`."""
    violations: list[str] = []
    for rel, path in _iter_app_python_files():
        if path.name in DOCSTRING_EXEMPT_NAMES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        if not tree.body:
            continue
        first = tree.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
            and first.end_lineno is not None
        ):
            doc_lines = first.end_lineno - first.lineno + 1
            ceiling = DOCSTRING_RATCHET_ALLOWLIST.get(rel, 100)
            if doc_lines > ceiling:
                violations.append(f"{rel}: {doc_lines} docstring lines (> {ceiling})")
    return violations


def check_file_size_ceiling() -> list[str]:
    """Check <= 1,000 physical lines across `app/` outside the ratchet allowlist."""
    violations: list[str] = [
        f"{rel}: forbidden in RATCHET_ALLOWLIST"
        for rel in RATCHET_ALLOWLIST
        if rel.startswith("app/services/include/")
    ]
    for rel, path in _iter_app_python_files():
        if rel in FILE_SIZE_EXEMPT_PATHS:
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        ceiling = RATCHET_ALLOWLIST.get(rel, 1000)
        if line_count > ceiling:
            violations.append(f"{rel}: {line_count} physical lines (> {ceiling})")
    return violations


def check_include_facade() -> list[str]:
    """Check <= 100 physical lines and no `__getattr__` in `include/__init__.py`."""
    violations: list[str] = []
    facade_path = APP_ROOT / "services" / "include" / "__init__.py"
    source = facade_path.read_text(encoding="utf-8")
    lines = source.splitlines()
    if len(lines) > 100:
        violations.append(
            f"app/services/include/__init__.py: {len(lines)} lines (> 100)"
        )
    tree = ast.parse(source, filename="app/services/include/__init__.py")
    func_names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    if "__getattr__" in func_names:
        violations.append(
            "app/services/include/__init__.py: forbidden __getattr__ lazy loader"
        )
    return violations


def check_persistence_isolation() -> list[str]:
    """Check `sqlite3` and connection helpers remain exclusively in `persistence.py`."""
    allowed = "app/host/persistence.py"
    forbidden_funcs = {"resolved_db_path", "_get_connection"}
    violations: list[str] = []
    for rel, path in _iter_app_python_files():
        if rel == allowed:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        violations.extend(
            f"{rel}: forbidden import '{mod}'"
            for mod in _extract_imports(tree, rel)
            if mod == "sqlite3" or mod.startswith("sqlite3.")
        )
        violations.extend(
            f"{rel}: forbidden function definition '{node.name}'"
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name in forbidden_funcs
        )
    return violations


def check_one_way_layering_dag() -> list[str]:
    """Check one-way dependency boundaries across `include`, `services`, and `host`."""
    violations: list[str] = []
    for rel, path in _iter_app_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        for target in _extract_imports(tree, rel):
            if rel.startswith("app/services/include/"):
                if target.startswith(("app.services.brokers", "app.workspace")):
                    violations.append(f"{rel} -> {target}")
            elif rel.startswith("app/services/"):
                if target.startswith("app.workspace"):
                    violations.append(f"{rel} -> {target}")
            elif rel.startswith("app/host/") and rel != "app/host/bootstrap.py":
                if target.startswith(("app.workspace", "app.services")):
                    violations.append(f"{rel} -> {target}")
    return violations


def main() -> int:
    """Run all architectural invariant checks and return 0 on success or 1 on failure."""
    checks = (
        ("FR-ARCH-DOCSTRING-CEILING", check_docstring_line_ceiling),
        ("FR-ARCH-FILE-SIZE-RATCHET", check_file_size_ceiling),
        ("FR-ARCH-FACADE-SIZE", check_include_facade),
        ("FR-ARCH-PERSISTENCE-ISOLATION", check_persistence_isolation),
        ("FR-ARCH-LAYERING-DAG", check_one_way_layering_dag),
    )
    failed = False
    for fr_id, fn in checks:
        violations = fn()
        if violations:
            failed = True
            for item in violations:
                logger.error("%s: violation %s", fr_id, item)
        else:
            logger.info("%s: passed", fr_id)
    return 1 if failed else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
