"""Extract runtime and configuration coupling graphs via AST analysis.

Traces to: P2-T02, Gate G2
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
    ".dev",
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

RUNTIME_KINDS = {
    "router_mount",
    "startup_hook",
    "shutdown_hook",
    "subscriber",
    "scheduled_job",
    "background_task",
    "callback",
    "factory",
    "worker",
    "subprocess",
}

CONFIG_KINDS = {
    "module_path",
    "provider_name",
    "profile",
    "feature_flag",
    "environment",
    "secret_reference",
    "allowlist",
}

PROFILES = {"research", "simulation", "demo", "live"}
ENVIRONMENTS = {"dev", "test", "staging", "production"}
SECRET_KEYWORDS = {
    "secret",
    "password",
    "token",
    "key",
    "credential",
    "auth_token",
    "jwt",
}
KNOWN_PROVIDERS = {"mt5", "metatrader", "ctrader", "binance", "dukascopy", "yahoo"}


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


class RuntimeConfigVisitor(ast.NodeVisitor):
    """AST visitor extracting runtime execution edges and configuration references."""

    def __init__(self, rel_path: str) -> None:
        """Initialize visitor with file path.

        Args:
            rel_path: Repo-relative file path.
        """
        self.rel_path = rel_path
        self.runtime_edges: list[dict[str, Any]] = []
        self.config_edges: list[dict[str, Any]] = []
        self.unexplained: list[dict[str, Any]] = []

    @override
    def visit_Call(self, node: ast.Call) -> None:
        """Process call nodes for runtime actions and configuration string arguments.

        Args:
            node: AST Call expression node.
        """
        func_name = self._resolve_func_name(node.func)
        self._check_runtime_calls(node, func_name)
        self._check_config_args(node)
        self.generic_visit(node)

    def _resolve_func_name(self, func_node: ast.AST) -> str:
        """Extract function name string from AST node.

        Args:
            func_node: Function AST node.

        Returns:
            Resolved function name string.
        """
        if isinstance(func_node, ast.Name):
            return func_node.id
        if isinstance(func_node, ast.Attribute):
            return func_node.attr
        return ""

    def _check_runtime_calls(self, node: ast.Call, func_name: str) -> None:
        """Identify runtime execution hooks, background tasks, and factories."""
        if func_name == "include_router":
            self.runtime_edges.append(
                {
                    "source": self.rel_path,
                    "kind": "router_mount",
                    "lineno": node.lineno,
                    "detail": "include_router",
                }
            )
        elif func_name in ("create_task", "add_task", "Thread", "Process"):
            self.runtime_edges.append(
                {
                    "source": self.rel_path,
                    "kind": "background_task",
                    "lineno": node.lineno,
                    "detail": func_name,
                }
            )
        elif (
            func_name in ("run", "Popen", "check_output", "check_call")
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
        ):
            self.runtime_edges.append(
                {
                    "source": self.rel_path,
                    "kind": "subprocess",
                    "lineno": node.lineno,
                    "detail": f"subprocess.{func_name}",
                }
            )
        elif "add_job" in func_name or "schedule" in func_name:
            self.runtime_edges.append(
                {
                    "source": self.rel_path,
                    "kind": "scheduled_job",
                    "lineno": node.lineno,
                    "detail": func_name,
                }
            )
        elif "subscribe" in func_name:
            self.runtime_edges.append(
                {
                    "source": self.rel_path,
                    "kind": "subscriber",
                    "lineno": node.lineno,
                    "detail": func_name,
                }
            )
        elif "callback" in func_name or "add_listener" in func_name:
            self.runtime_edges.append(
                {
                    "source": self.rel_path,
                    "kind": "callback",
                    "lineno": node.lineno,
                    "detail": func_name,
                }
            )
        elif func_name.startswith("create_") or func_name.endswith("_factory"):
            self.runtime_edges.append(
                {
                    "source": self.rel_path,
                    "kind": "factory",
                    "lineno": node.lineno,
                    "detail": func_name,
                }
            )
        elif "worker" in func_name.lower():
            self.runtime_edges.append(
                {
                    "source": self.rel_path,
                    "kind": "worker",
                    "lineno": node.lineno,
                    "detail": func_name,
                }
            )

    def _check_config_args(self, node: ast.Call) -> None:
        """Inspect string constants passed into function calls."""
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                s_val = arg.value.lower()
                if s_val in PROFILES:
                    self.config_edges.append(
                        {
                            "source": self.rel_path,
                            "kind": "profile",
                            "lineno": node.lineno,
                            "name": s_val,
                        }
                    )
                elif s_val in ENVIRONMENTS:
                    self.config_edges.append(
                        {
                            "source": self.rel_path,
                            "kind": "environment",
                            "lineno": node.lineno,
                            "name": s_val,
                        }
                    )
                elif s_val in KNOWN_PROVIDERS:
                    self.config_edges.append(
                        {
                            "source": self.rel_path,
                            "kind": "provider_name",
                            "lineno": node.lineno,
                            "name": s_val,
                        }
                    )

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Inspect function definitions and decorators for lifecycle hooks.

        Args:
            node: AST FunctionDef node.
        """
        for decorator in node.decorator_list:
            dec_name = self._resolve_func_name(decorator)
            if "startup" in dec_name:
                self.runtime_edges.append(
                    {
                        "source": self.rel_path,
                        "kind": "startup_hook",
                        "lineno": node.lineno,
                        "detail": node.name,
                    }
                )
            elif "shutdown" in dec_name:
                self.runtime_edges.append(
                    {
                        "source": self.rel_path,
                        "kind": "shutdown_hook",
                        "lineno": node.lineno,
                        "detail": node.name,
                    }
                )

        if node.name.startswith("create_") or node.name.endswith("_factory"):
            self.runtime_edges.append(
                {
                    "source": self.rel_path,
                    "kind": "factory",
                    "lineno": node.lineno,
                    "detail": node.name,
                }
            )

        self.generic_visit(node)

    @override
    def visit_Assign(self, node: ast.Assign) -> None:
        """Inspect assignments for secrets, allowlists, and feature flags.

        Args:
            node: AST Assign node.
        """
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id.lower()
                if any(sec in var_name for sec in SECRET_KEYWORDS):
                    self.config_edges.append(
                        {
                            "source": self.rel_path,
                            "kind": "secret_reference",
                            "lineno": node.lineno,
                            "name": target.id,
                        }
                    )
                elif "allowlist" in var_name or "whitelist" in var_name:
                    self.config_edges.append(
                        {
                            "source": self.rel_path,
                            "kind": "allowlist",
                            "lineno": node.lineno,
                            "name": target.id,
                        }
                    )
                elif "flag" in var_name or "enable" in var_name or "allow_" in var_name:
                    self.config_edges.append(
                        {
                            "source": self.rel_path,
                            "kind": "feature_flag",
                            "lineno": node.lineno,
                            "name": target.id,
                        }
                    )
                elif var_name in ("module_path", "package_path"):
                    self.config_edges.append(
                        {
                            "source": self.rel_path,
                            "kind": "module_path",
                            "lineno": node.lineno,
                            "name": target.id,
                        }
                    )

        self.generic_visit(node)


def scan_runtime_and_config(root_path: Path) -> dict[str, Any]:
    """Scan Python files for runtime execution and configuration patterns.

    Args:
        root_path: Path to repository root.

    Returns:
        Dictionary containing runtime edges, configuration edges,
        and unexplained entries.
    """
    runtime_edges: list[dict[str, Any]] = []
    config_edges: list[dict[str, Any]] = []
    unexplained: list[dict[str, Any]] = []

    py_files: list[Path] = []
    for p in root_path.rglob("*.py"):
        rel_parts = p.relative_to(root_path).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        py_files.append(p)

    py_files.sort()

    for py_file in py_files:
        rel_str = py_file.relative_to(root_path).as_posix()
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel_str)
            visitor = RuntimeConfigVisitor(rel_str)
            visitor.visit(tree)
            runtime_edges.extend(visitor.runtime_edges)
            config_edges.extend(visitor.config_edges)
            unexplained.extend(visitor.unexplained)
        except SyntaxError as e:
            print(f"SYNTAX_ERROR: {rel_str}:{e.lineno} {e.msg}", file=sys.stderr)
            sys.exit(1)

    runtime_edges.sort(key=lambda r: (r["source"], r["kind"], r["lineno"], r["detail"]))
    config_edges.sort(key=lambda c: (c["source"], c["kind"], c["lineno"], c["name"]))
    unexplained.sort(key=lambda u: (u.get("source", ""), u.get("lineno", 0)))

    commit_hash = get_git_commit(root_path)

    return {
        "schema_version": 1,
        "commit": commit_hash,
        "runtime_edges": runtime_edges,
        "configuration_edges": config_edges,
        "unexplained": unexplained,
    }


def main() -> int:
    """CLI entry point for runtime/configuration graph extraction.

    Returns:
        Exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Extract runtime and configuration graphs."
    )
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    output_path = Path(args.output).resolve()

    graph = scan_runtime_and_config(root_path)

    if graph["unexplained"]:
        print(
            f"UNEXPLAINED_ENTRIES: {len(graph['unexplained'])} found",
            file=sys.stderr,
        )
        sys.exit(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
