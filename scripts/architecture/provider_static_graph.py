"""Extract static Python dependency graph via AST traversal without importing modules.

Traces to: P2-T01, Gate G2
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, override

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "out",
    "build",
    "dist",
}

EDGE_KINDS = {
    "import",
    "from_import",
    "dynamic_import",
    "string_module",
    "lazy_export",
    "decorator_registration",
}


def get_git_commit(root: Path) -> str:
    """Get current git commit hash, falling back to 'unknown' if not a git repo.

    Args:
        root: Repository root path.

    Returns:
        Git commit hash or 'unknown'.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.SubprocessError, OSError:
        return "unknown"


def is_type_checking_test(node: ast.AST) -> bool:
    """Check if AST test expression represents a TYPE_CHECKING check.

    Args:
        node: AST expression to check.

    Returns:
        True if expression checks TYPE_CHECKING, False otherwise.
    """
    return (isinstance(node, ast.Name) and node.id == "TYPE_CHECKING") or (
        isinstance(node, ast.Attribute) and node.attr == "TYPE_CHECKING"
    )


def _extract_string_literals(node: ast.AST) -> list[str]:
    """Recursively extract all string constant values within an AST subtree.

    Args:
        node: AST node to inspect.

    Returns:
        List of string literal values found.
    """
    strings: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            strings.append(child.value)
    return strings


class StaticImportVisitor(ast.NodeVisitor):
    """AST visitor extracting static imports, lazy exports, and dynamic imports."""

    def __init__(self, rel_path: str) -> None:
        """Initialize visitor with file path.

        Args:
            rel_path: Repo-relative file path.
        """
        self.rel_path = rel_path
        self.edges: list[dict[str, Any]] = []
        self.dynamic_imports: list[dict[str, Any]] = []
        self.lazy_exports: list[dict[str, Any]] = []
        self.string_modules: list[str] = []
        self._type_checking_depth = 0
        self._exports_dict_found = False
        self._lazy_class_modules: set[str] = set()

    @override
    def visit_If(self, node: ast.If) -> None:
        """Handle if statements and track TYPE_CHECKING guard depth.

        Args:
            node: AST If statement node.
        """
        is_tc = is_type_checking_test(node.test)
        if is_tc:
            self._type_checking_depth += 1
            for stmt in node.body:
                self.visit(stmt)
            self._type_checking_depth -= 1
            for stmt in node.orelse:
                self.visit(stmt)
        else:
            self.generic_visit(node)

    @override
    def visit_Import(self, node: ast.Import) -> None:
        """Handle plain import statements.

        Args:
            node: AST Import statement node.
        """
        for alias in node.names:
            target = alias.name
            self.edges.append(
                {
                    "source": self.rel_path,
                    "target": target,
                    "kind": "import",
                    "lineno": node.lineno,
                    "type_checking": self._type_checking_depth > 0,
                    "resolved_symbol": None,
                }
            )
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Handle from ... import ... statements.

        Args:
            node: AST ImportFrom statement node.
        """
        module = node.module or ""
        level = node.level
        target = ("." * level) + module if level > 0 else module
        for alias in node.names:
            self.edges.append(
                {
                    "source": self.rel_path,
                    "target": target,
                    "kind": "from_import",
                    "lineno": node.lineno,
                    "type_checking": self._type_checking_depth > 0,
                    "resolved_symbol": alias.name,
                }
            )
        self.generic_visit(node)

    @override
    def visit_Call(self, node: ast.Call) -> None:
        """Handle call expressions for dynamic imports and lazy module instantiations.

        Args:
            node: AST Call expression node.
        """
        self._check_lazy_wrapper_call(node)
        self._check_dynamic_import_call(node)
        self.generic_visit(node)

    def _check_lazy_wrapper_call(self, node: ast.Call) -> None:
        """Check for _LazyModule instances."""
        if isinstance(node.func, ast.Name) and "Lazy" in node.func.id:
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    self._lazy_class_modules.add(arg.value)
                    self.edges.append(
                        {
                            "source": self.rel_path,
                            "target": arg.value,
                            "kind": "string_module",
                            "lineno": node.lineno,
                            "type_checking": False,
                            "resolved_symbol": None,
                        }
                    )

    def _check_dynamic_import_call(self, node: ast.Call) -> None:
        """Check for importlib.import_module or __import__ calls."""
        is_dyn = (isinstance(node.func, ast.Name) and node.func.id == "__import__") or (
            isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"
        )
        if not is_dyn or not node.args:
            return

        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            target = first_arg.value
            self.edges.append(
                {
                    "source": self.rel_path,
                    "target": target,
                    "kind": "dynamic_import",
                    "lineno": node.lineno,
                    "type_checking": self._type_checking_depth > 0,
                    "resolved_symbol": None,
                }
            )
            self.dynamic_imports.append(
                {
                    "source": self.rel_path,
                    "target": target,
                    "lineno": node.lineno,
                    "literal": True,
                }
            )
        elif self._exports_dict_found:
            pass
        elif self.string_modules:
            for mod_target in self.string_modules:
                self.dynamic_imports.append(
                    {
                        "source": self.rel_path,
                        "target": mod_target,
                        "lineno": node.lineno,
                        "literal": False,
                    }
                )
        elif self._lazy_class_modules:
            for mod_target in self._lazy_class_modules:
                self.dynamic_imports.append(
                    {
                        "source": self.rel_path,
                        "target": mod_target,
                        "lineno": node.lineno,
                        "literal": False,
                    }
                )
        elif self.rel_path.startswith("tests/") or self.rel_path.startswith("scripts/"):
            pass
        else:
            print(
                f"UNEXPLAINED_DYNAMIC_IMPORT: {self.rel_path}:{node.lineno}",
                file=sys.stderr,
            )
            sys.exit(2)

    @override
    def visit_Assign(self, node: ast.Assign) -> None:
        """Handle variable assignments for _EXPORTS and _FACTORIES registrations.

        Args:
            node: AST Assign node.
        """
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id in ("_EXPORTS", "_LAZY_EXPORTS"):
                    self._parse_exports_dict(node)
                elif target.id.startswith("_FACTOR"):
                    self._parse_factories_dict(node)
        self.generic_visit(node)

    def _parse_exports_dict(self, node: ast.Assign) -> None:
        """Parse lazy _EXPORTS dictionary mappings."""
        self._exports_dict_found = True
        if not isinstance(node.value, ast.Dict):
            return
        for k, v in zip(node.value.keys, node.value.values, strict=True):
            sym_name = (
                k.value
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
                else None
            )
            mod_target = None
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                mod_target = v.value
            elif (
                isinstance(v, ast.Tuple)
                and v.elts
                and isinstance(v.elts[0], ast.Constant)
                and isinstance(v.elts[0].value, str)
            ):
                mod_target = v.elts[0].value

            if sym_name and mod_target:
                self.edges.append(
                    {
                        "source": self.rel_path,
                        "target": mod_target,
                        "kind": "lazy_export",
                        "lineno": node.lineno,
                        "type_checking": False,
                        "resolved_symbol": sym_name,
                    }
                )
                self.lazy_exports.append(
                    {
                        "source": self.rel_path,
                        "symbol": sym_name,
                        "target": mod_target,
                        "lineno": node.lineno,
                    }
                )

    def _parse_factories_dict(self, node: ast.Assign) -> None:
        """Parse factory registration dictionary mappings."""
        if not isinstance(node.value, ast.Dict):
            return
        for v in node.value.values:
            strs = _extract_string_literals(v)
            for s in strs:
                if "." in s or s in (
                    "MetaTrader5",
                    "ctrader_open_api",
                    "binance",
                    "yfinance",
                    "dukascopy",
                ):
                    self.string_modules.append(s)
                    self.edges.append(
                        {
                            "source": self.rel_path,
                            "target": s,
                            "kind": "string_module",
                            "lineno": node.lineno,
                            "type_checking": False,
                            "resolved_symbol": None,
                        }
                    )


def scan_repository(root_path: Path) -> dict[str, Any]:
    """Scan all Python files in the repository and build the static graph.

    Args:
        root_path: Path to repository root.

    Returns:
        Dictionary containing static graph nodes, edges, dynamic imports,
        and lazy exports.
    """
    nodes: list[str] = []
    edges: list[dict[str, Any]] = []
    dynamic_imports: list[dict[str, Any]] = []
    lazy_exports: list[dict[str, Any]] = []

    py_files: list[Path] = []
    for p in root_path.rglob("*.py"):
        rel_parts = p.relative_to(root_path).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        py_files.append(p)

    py_files.sort()

    for py_file in py_files:
        rel_str = py_file.relative_to(root_path).as_posix()
        nodes.append(rel_str)
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel_str)
            visitor = StaticImportVisitor(rel_str)
            visitor.visit(tree)
            edges.extend(visitor.edges)
            dynamic_imports.extend(visitor.dynamic_imports)
            lazy_exports.extend(visitor.lazy_exports)
        except SyntaxError as e:
            print(f"SYNTAX_ERROR: {rel_str}:{e.lineno} {e.msg}", file=sys.stderr)
            sys.exit(1)

    nodes.sort()
    edges.sort(
        key=lambda e: (
            e["source"],
            e["target"],
            e["kind"],
            e["lineno"],
            e["type_checking"],
            e["resolved_symbol"] or "",
        )
    )
    dynamic_imports.sort(key=lambda d: (d["source"], d["target"], d["lineno"]))
    lazy_exports.sort(
        key=lambda item: (
            item["source"],
            item["symbol"],
            item["target"],
            item["lineno"],
        )
    )

    commit_hash = get_git_commit(root_path)

    return {
        "schema_version": 1,
        "commit": commit_hash,
        "nodes": nodes,
        "edges": edges,
        "dynamic_imports": dynamic_imports,
        "lazy_exports": lazy_exports,
    }


def main() -> int:
    """CLI entry point for static graph extraction.

    Returns:
        Exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Extract static Python dependency graph."
    )
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    output_path = Path(args.output).resolve()

    graph = scan_repository(root_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
